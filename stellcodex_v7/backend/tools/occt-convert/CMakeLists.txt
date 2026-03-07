cmake_minimum_required(VERSION 3.16)
project(occt_convert LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenCASCADE REQUIRED)

add_executable(occt-convert occt_convert.cpp)

target_include_directories(occt-convert PRIVATE ${OpenCASCADE_INCLUDE_DIR})

set(OCCT_LINK_LIBS
  TKernel
  TKMath
  TKGeomBase
  TKG2d
  TKG3d
  TKBRep
  TKTopAlgo
  TKXSBase
  TKXCAF
  TKCAF
  TKLCAF
  TKCDF
  TKDE
  TKDEGLTF
  TKDESTEP
  TKDEIGES
  TKRWMesh
)

target_link_libraries(occt-convert PRIVATE ${OCCT_LINK_LIBS})
