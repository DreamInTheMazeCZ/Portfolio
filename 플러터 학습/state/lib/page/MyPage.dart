import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:state/controller/UserController.dart';

class MyPage extends StatelessWidget {
   
  MyPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('마이페이지')),
      body: Container(
        child: Column(
          children: [
            Text('내 포인트는?'),
            // GetBuilder<UserController>(
            //   builder: (controller) {
            //     return Text(controller.userPoint.toString());
            //   }
            // ),

            // 위 방식으로 선언하면 Get.find가 필요 없음
            // setState() 없이도 전역변수의 값을 변화시킬 수 있음
            // 앱 전체에 적용하는 위젯 독립적인 변수 사용 가능

            // setState와 UserController 상속을 통해
            // Stateful Widget 형으로도 구현 가능

            GetBuilder<UserController>(
              builder: (controller) {
                // controller.useUserPoint();
                return GestureDetector(
                  onTap: () {
                    controller.useUserPoint();
                  },
                  child: Column(
                    children: [
                      Text(controller.userPoint.toString()),
                      Text('포인트 사용')
                    ]
                  )
                );
              }
            )
          ]
        )
      )
    );
  }
}