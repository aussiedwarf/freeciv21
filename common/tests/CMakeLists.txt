set(CMAKE_AUTOMOC ON)

add_executable(test_dio dio.cpp)
target_link_libraries(test_dio PRIVATE common Qt6::Test)
add_test(NAME test_dio COMMAND test_dio)

add_executable(test_combat_math combat_math.cpp)
target_link_libraries(test_combat_math PRIVATE common Qt6::Test)
add_test(NAME test_combat_math COMMAND test_combat_math)
