#include "openfhe.h"
#include "ciphertext-ser.h"
#include "cryptocontext-ser.h"
#include "key/key-ser.h"
#include "scheme/ckksrns/ckksrns-ser.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <vector>
using namespace lbcrypto;
using Clock = std::chrono::steady_clock;

static std::vector<int> candidates() {
    std::vector<int> a{1,2,3,4,5,7,8,9,15,16,17,31,32,33,63,64}, out;
    for (int x : a) { out.push_back(-x); out.push_back(x); }
    std::sort(out.begin(), out.end(), [](int x,int y){ return std::tuple(std::abs(x),x)<std::tuple(std::abs(y),y); });
    return out;
}
static double median(std::vector<double> x) { std::sort(x.begin(),x.end()); return (x[24]+x[25])/2; }
static double med(std::vector<double> x) { std::sort(x.begin(),x.end()); size_t n=x.size(); return n%2?x[n/2]:(x[n/2-1]+x[n/2])/2; }
static std::vector<int> parsePath(const std::string& s) {
    std::vector<int> v; std::stringstream ss(s); std::string x;
    while(std::getline(ss,x,';')) if(!x.empty()) v.push_back(std::stoi(x));
    return v;
}
int main(int argc,char**argv) try {
    const std::string outdir = argc>1 ? argv[1] : "data";
    const std::string mode = argc>2 ? argv[2] : "primitive";
    std::filesystem::create_directories(outdir);
    CCParams<CryptoContextCKKSRNS> p;
    p.SetSecurityLevel(HEStd_128_classic); p.SetRingDim(16384); p.SetBatchSize(8192);
    p.SetMultiplicativeDepth(3); p.SetScalingModSize(50); p.SetKeySwitchTechnique(HYBRID); p.SetNumLargeDigits(3);
    auto cc=GenCryptoContext(p); cc->Enable(PKE); cc->Enable(KEYSWITCH); cc->Enable(LEVELEDSHE);
    if (cc->GetRingDimension()!=16384) throw std::runtime_error("OpenFHE rejected requested ring dimension 16384");
    auto kp=cc->KeyGen(); if(!kp.good()) throw std::runtime_error("KeyGen failed");
    auto cand=candidates();
    std::mt19937 gen(1); std::uniform_real_distribution<double> dist(-1,1);
    std::vector<double> input(8192); for(auto&x:input)x=dist(gen);
    auto pt=cc->MakeCKKSPackedPlaintext(input); auto ct=cc->Encrypt(kp.publicKey,pt);
    if(mode=="composed") {
        cc->EvalRotateKeyGen(kp.secretKey,cand);
        std::ifstream in(outdir+"/composition_paths_input.csv"); if(!in) throw std::runtime_error("missing composition_paths_input.csv");
        std::ofstream csv(outdir+"/composed_rotation_bench.csv");
        csv<<"path_id,path,hop_count,total_rotation,predicted_us,measured_median_us,measured_mean_us,stddev_us,se_us,ratio,max_abs_error,correctness,warmups,runs\n";
        std::string line; std::getline(in,line);
        while(std::getline(in,line)) {
            auto comma=line.find(','); if(comma==std::string::npos) continue;
            int id=std::stoi(line.substr(0,comma)); auto path=parsePath(line.substr(comma+1));
            for(int i=0;i<5;i++){ auto z=ct; for(int k:path)z=cc->EvalRotate(z,k); }
            std::vector<double> ts; Ciphertext<DCRTPoly> z;
            for(int i=0;i<20;i++){ z=ct; auto a=Clock::now(); for(int k:path)z=cc->EvalRotate(z,k); auto b=Clock::now(); ts.push_back(std::chrono::duration<double,std::micro>(b-a).count()); }
            double mean=std::accumulate(ts.begin(),ts.end(),0.0)/ts.size(),ss=0;for(double t:ts)ss+=(t-mean)*(t-mean);
            Plaintext dec;cc->Decrypt(kp.secretKey,z,&dec);dec->SetLength(8192);auto got=dec->GetCKKSPackedValue();
            int total=std::accumulate(path.begin(),path.end(),0);double err=0;for(size_t i=0;i<input.size();i++){size_t j=(i+(total%8192)+8192)%8192;err=std::max(err,std::abs(got[i].real()-input[j]));}
            std::ifstream prim(outdir+"/primitive_rotation_bench.csv");std::string pl;std::getline(prim,pl);double predicted=0;
            while(std::getline(prim,pl)){std::stringstream ps(pl);std::string f;std::getline(ps,f,',');int r=std::stoi(f);std::getline(ps,f,',');std::getline(ps,f,',');if(std::find(path.begin(),path.end(),r)!=path.end())for(int k:path)if(k==r)predicted+=std::stod(f);}
            csv<<id<<",\"";for(size_t i=0;i<path.size();i++){if(i)csv<<';';csv<<path[i];}csv<<"\","<<path.size()<<','<<total<<','<<predicted<<','<<med(ts)<<','<<mean<<','<<std::sqrt(ss/(ts.size()-1))<<','<<std::sqrt(ss/(ts.size()-1))/std::sqrt(ts.size())<<','<<med(ts)/predicted<<','<<std::setprecision(12)<<err<<','<<(err<1e-6?"PASS":"FAIL")<<",5,20\n";
            std::cout<<"composed path_id="<<id<<" hops="<<path.size()<<" error="<<err<<std::endl;
        }
        return 0;
    }
    if(mode=="direct-extra") {
        std::ifstream in(outdir+"/all_required_missing.txt");std::vector<int> req;int x;while(in>>x)req.push_back(x);
        cc->EvalRotateKeyGen(kp.secretKey,req);
        std::ofstream csv(outdir+"/primitive_rotation_bench_extra.csv");csv<<"rotation,serialized_bytes,median_us,mean_us,stddev_us,se_us,warmups,runs,ring_dim,slots\n";
        std::ofstream cor(outdir+"/correctness_extra.csv");cor<<"rotation,hops,max_abs_error,passed\n";
        for(int k:req){for(int i=0;i<10;i++){auto z=cc->EvalRotate(ct,k);(void)z;}std::vector<double>ts;Ciphertext<DCRTPoly>z;for(int i=0;i<50;i++){auto a=Clock::now();z=cc->EvalRotate(ct,k);auto b=Clock::now();ts.push_back(std::chrono::duration<double,std::micro>(b-a).count());}
            double mean=std::accumulate(ts.begin(),ts.end(),0.0)/ts.size(),ss=0;for(double t:ts)ss+=(t-mean)*(t-mean);Plaintext dec;cc->Decrypt(kp.secretKey,z,&dec);dec->SetLength(8192);auto got=dec->GetCKKSPackedValue();double err=0;for(size_t i=0;i<input.size();i++){size_t j=(i+(k%8192)+8192)%8192;err=std::max(err,std::abs(got[i].real()-input[j]));}
            CryptoContextImpl<DCRTPoly>::ClearEvalAutomorphismKeys();cc->EvalRotateKeyGen(kp.secretKey,{k});std::ostringstream os(std::ios::binary);cc->SerializeEvalAutomorphismKey(os,SerType::BINARY,kp.secretKey->GetKeyTag());auto bytes=os.str().size();CryptoContextImpl<DCRTPoly>::ClearEvalAutomorphismKeys();cc->EvalRotateKeyGen(kp.secretKey,req);
            csv<<k<<','<<bytes<<','<<med(ts)<<','<<mean<<','<<std::sqrt(ss/(ts.size()-1))<<','<<std::sqrt(ss/(ts.size()-1))/std::sqrt(ts.size())<<",10,50,16384,8192\n";cor<<k<<",1,"<<std::setprecision(12)<<err<<','<<(err<1e-6?"true":"false")<<"\n";std::cout<<"extra "<<k<<" error="<<err<<std::endl;}
        return 0;
    }
    cc->EvalRotateKeyGen(kp.secretKey,cand);
    std::ofstream csv(outdir+"/primitive_rotation_bench.csv");
    csv<<"rotation,serialized_bytes,median_us,mean_us,stddev_us,se_us,warmups,runs,ring_dim,slots\n";
    std::ofstream cor(outdir+"/correctness.csv"); cor<<"rotation,hops,max_abs_error,passed\n";
    for(int k:cand){
        for(int i=0;i<10;i++){ auto z=cc->EvalRotate(ct,k); (void)z; }
        std::vector<double> ts; Ciphertext<DCRTPoly> z;
        for(int i=0;i<50;i++){ auto a=Clock::now(); z=cc->EvalRotate(ct,k); auto b=Clock::now(); ts.push_back(std::chrono::duration<double,std::micro>(b-a).count()); }
        double mean=std::accumulate(ts.begin(),ts.end(),0.0)/ts.size(), ss=0; for(double t:ts)ss+=(t-mean)*(t-mean);
        Plaintext dec; cc->Decrypt(kp.secretKey,z,&dec); dec->SetLength(8192); auto got=dec->GetCKKSPackedValue();
        double err=0; for(size_t i=0;i<input.size();i++){ size_t j=(i+(k%8192)+8192)%8192; err=std::max(err,std::abs(got[i].real()-input[j])); }
        CryptoContextImpl<DCRTPoly>::ClearEvalAutomorphismKeys(); cc->EvalRotateKeyGen(kp.secretKey,{k});
        std::ostringstream os(std::ios::binary); cc->SerializeEvalAutomorphismKey(os,SerType::BINARY,kp.secretKey->GetKeyTag()); auto bytes=os.str().size();
        CryptoContextImpl<DCRTPoly>::ClearEvalAutomorphismKeys(); cc->EvalRotateKeyGen(kp.secretKey,cand);
        csv<<k<<','<<bytes<<','<<median(ts)<<','<<mean<<','<<std::sqrt(ss/(ts.size()-1))<<','<<std::sqrt(ss/(ts.size()-1))/std::sqrt(ts.size())<<",10,50,16384,8192\n";
        cor<<k<<",1,"<<std::setprecision(12)<<err<<','<<(err<1e-6?"true":"false")<<"\n";
        std::cout<<"rotation "<<k<<" median_us="<<median(ts)<<" bytes="<<bytes<<" error="<<err<<std::endl;
    }
    return 0;
} catch(const std::exception&e){ std::cerr<<"FATAL: "<<e.what()<<std::endl; return 1; }
