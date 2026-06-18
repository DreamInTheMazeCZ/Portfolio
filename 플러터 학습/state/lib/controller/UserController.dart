import 'package:flutter/material.dart';
import 'package:get/get.dart';

class UserController extends GetxController {

  int userPoint = 0;

  Future<void> addUserPoint() async{

    userPoint ++;
    update();
    print(userPoint);
  }

  Future<void> useUserPoint() async{

    userPoint --;
    update();
    print(userPoint);
  }
}

// 하기 방법도 가능
// void addUserPoint() {
// }