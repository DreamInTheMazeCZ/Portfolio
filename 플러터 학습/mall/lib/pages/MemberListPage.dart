import 'package:flutter/material.dart';
import 'package:get/get.dart';

class MemberListPage extends StatelessWidget {
  MemberListPage({super.key});

  final List<String> member = ['김철수', '김영희', '박상희'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('멤버 리스트')),
      body: Column(
        children: [
          Text('멤버 리스트'),
          Expanded(
            // ListView.builder를 통해 반복문 활용
            // builder는 스크롤하기 전에는 렌더링하지 않기 때문에 자원효율적이라고 함
            child: ListView.builder(
              itemCount: member.length,
              itemBuilder: (context, index) {
                return Container(
                  margin: EdgeInsets.symmetric(vertical: 4),
                  height: 30,
                  decoration: BoxDecoration(
                    color: Colors.lightBlueAccent,
                    border: Border.all(color: Colors.black),
                  ),
                  child: Center(child: Text(member[index]))
                );
              }
            )
          ),
          Container(
            height: 50,
            width: Get.width,
            color: Colors.brown,
            child: Center(child: Text('구글 광고'))
          )
        ]
      )
    );
  }
}