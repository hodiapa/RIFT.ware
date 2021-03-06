# 
# (c) Copyright RIFT.io, 2013-2016, All Rights Reserved
#
# Author(s): Anil Gunturu
# Creation Date: 8/29/2013
# 

include_directories(BEFORE ${CMAKE_CURRENT_BINARY_DIR})
set(EXTRA_LIBS
  rwyang

  # RIFT-5092 - this should be using rift_pkg_check_modules
  ${CMAKE_INSTALL_PREFIX}/usr/lib/libprotobuf-c.so)

##
# Add the proto subdir alone first - needed to build pb2c
##
set(subdirs proto)
rift_add_subdirs(SUBDIR_LIST ${subdirs})
rift_files_prepend_path(pb2c_proto_c_files proto ${pb2c_proto_c_files})

##
# Create the pb2c tool
##
add_executable(pb2c pb2c.c ${pb2c_proto_c_files})
target_link_libraries(pb2c 
  ${RIFT_SUBMODULE_BINARY_ROOT}/yangtools/pb2c/proto/libpb2c_proto.a
  ${EXTRA_LIBS})
add_dependencies(pb2c pb2c_proto)

install(TARGETS pb2c DESTINATION usr/bin COMPONENT pb2c-1.0)


##
# Parse the example proto files
##
set(subdirs sample_protobufs)
rift_add_subdirs(SUBDIR_LIST ${subdirs})

##
# Create the pb2c test tool
##
add_executable(pb2c_test pb2c_test.cpp pb2c_test_cfiles.c)
target_link_libraries(pb2c_test 
  ${RIFT_SUBMODULE_BINARY_ROOT}/yangtools/pb2c/proto/libpb2c_proto.a
  ${EXTRA_LIBS})
add_dependencies(pb2c_test pb2c_protoex)
target_include_directories(pb2c_test BEFORE PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/sample_protobufs)
# Don't have rwmsg lib here to link with these

rift_unittest(unittest_pb2c
  TEST_ARGS ${CMAKE_CURRENT_BINARY_DIR}/pb2c_test
#  --gtest_output=xml:${RIFT_UNITTEST_DIR}/rwtrace/unittest.xml
  DEPENDS pb2c_test
)

# needs -I with google protobuf headers
#add_executable(dso_dump dso_dump.cpp descriptor.pb-c.h ) # descriptor.pb.cc)
#target_link_libraries(dso_dump ${EXTRA_LIBS})
#install(TARGETS dso_dump DESTINATION usr/bin COMPONENT riftcli-1.0)

# A custom target for generated .h files for descriptor.proto and
# rwpbapi.proto.  This can be a dependency for other proto files that
# import descriptor.proto and rwpbabi.proto
add_custom_target(rwproto DEPENDS pb2c pb2c_proto)

