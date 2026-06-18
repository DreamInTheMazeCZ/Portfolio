import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'package:mall/pages/MemberListPage.dart';
import 'package:mall/pages/StoreListPage.dart';
import 'package:mall/pages/MyPage.dart';
import 'package:mall/components/ProductWidgets.dart';
import 'package:mall/vo/Product.dart';

class MainPage extends StatelessWidget {
  
  MainPage({super.key});

  Product product1 = Product(
    productName: '의자',
    imagePath: 'assets/images/chair.jpg',
    price:'3,000원'
  );

  Product product2 = Product(
    productName: '냉장고',
    imagePath: 'assets/images/ref.jpg',
    price:'5,000원'
  );

  Product product3 = Product(
    productName: '자동차',
    imagePath: 'assets/images/car.jpg',
    price:'6,000원'
  );

  Product product4 = Product(
    productName: '에어컨',
    imagePath: 'assets/images/aircon.jpg',
    price:'7,000원'
  );

  // 데이터 목록
  // List<String> nameGroup = ['의자', '냉장고', '자동차', '에어컨'];
  // List<String> imagePathGroup = [
  //   'assets/images/chair.jpg',
  //   'assets/images/ref.jpg',
  //   'assets/images/car.jpg',
  //   'assets/images/aircon.jpg',
  // ];
  // List<String> priceGroup = [
  //   '3,000원',
  //   '5,000원',
  //   '6,000원',
  //   '7,000원',
  // ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("사무실쇼핑몰"),centerTitle: true,backgroundColor: Colors.orangeAccent,),
      body: Container(
        padding: EdgeInsets.symmetric(horizontal: 10),
        child: Column(
          children: [
            SizedBox(height: 50,),
            Row(
              children: [
                ProductWidgets(item:product1),
                SizedBox(width: 10,),
                ProductWidgets(item:product2),
              ],
            ),
            SizedBox(height: 50,),
            Row(
              children: [
                ProductWidgets(item:product3),
                SizedBox(width: 10,),
                ProductWidgets(item:product4),
              ],
            ),
            SizedBox(height: 50,),
            GestureDetector(
              onTap: (){
                Get.to( () => MemberListPage());
              },
              child: Text('회원목록 보기', style: TextStyle(color: Colors.blue, fontSize: 26))
            ),
            SizedBox(height: 25,),
            GestureDetector(
              onTap: (){
                Get.to( () => StoreListPage());
              },
              child: Text('매장목록 보기', style: TextStyle(color: Colors.blue, fontSize: 26))
            ),
            SizedBox(height: 25,),
            GestureDetector(
              onTap: (){
                Get.to( () => MyPage(name:'홍길동', ages:30));
              },
              child: Text('마이 페이지', style: TextStyle(color: Colors.blue, fontSize: 26))
            ),
          ]
        ),
      ),
    );
  }
}