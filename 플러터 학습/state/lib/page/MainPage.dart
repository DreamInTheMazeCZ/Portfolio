import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:state/controller/UserController.dart';

import 'package:state/page/MyPage.dart';

class MainPage extends StatefulWidget {
  const MainPage({super.key});

  @override
  State<MainPage> createState() => _MainPage();
}

class _MainPage extends State<MainPage> {
  
  UserController userController = Get.find<UserController>();

  @override
  void initState() {
    super.initState();
    print(userController.userPoint);
  }


  @override
  Widget build(BuildContext context) {
    return GetBuilder<UserController>(
      builder: (container) {
        return Scaffold(
          appBar: AppBar(title: const Text('Mainpage')),
          body: Column(
            children: [
              Container(
                child: Text(userController.userPoint.toString())
              ),
              Container(
                child: Text('내 포인트')
              ),
              
              GestureDetector(
                onTap: (){
                  setState(() {
                    userController.addUserPoint();
                  });
                },
                child: Text('포인트 모으기')
              ),

              GestureDetector(
                onTap: () {
                  Get.to(() => MyPage());
                },
                child: Text('마이페이지로 넘어가기')
              ),
            ]
          )
        );
      }
    );
  }
}