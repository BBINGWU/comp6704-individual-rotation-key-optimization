cmake_minimum_required(VERSION 3.16)
project(rotation_key_optimization LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(OpenFHE CONFIG REQUIRED)
add_executable(benchmark_rotations src/benchmark_rotations.cpp)
target_include_directories(benchmark_rotations PRIVATE
  ${OpenFHE_INCLUDE}
  ${OpenFHE_INCLUDE}/core ${OpenFHE_INCLUDE}/pke ${OpenFHE_INCLUDE}/binfhe
  ${OpenFHE_INCLUDE}/third-party/include)
separate_arguments(OpenFHE_CXX_FLAGS_LIST NATIVE_COMMAND "${OpenFHE_CXX_FLAGS}")
target_compile_options(benchmark_rotations PRIVATE ${OpenFHE_CXX_FLAGS_LIST})
target_link_libraries(benchmark_rotations PRIVATE OPENFHEcore OPENFHEpke OPENFHEbinfhe)

