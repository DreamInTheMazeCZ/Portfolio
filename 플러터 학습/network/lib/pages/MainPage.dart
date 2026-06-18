import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:get/get.dart';

import '../service/HttpService.dart';
import '../controller/DataController.dart';

import 'dart:convert';

class MainPage extends StatefulWidget {

  const MainPage({super.key});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('http 요청 예제')),
      body: Column(
        children: [
          GestureDetector(
            onTap: () async {
              productModel = await httpService.getProductList();
              setState( () => {});
            },
            child: Text('요청하기')
          ),

          if (productModel != null)
          Expanded(
            child: ListView.builder(
              
              itemCount: productModel?.products?.length??0,
              itemBuilder: (context, index) {
                return Container(
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 20),
                  margin: EdgeInsets.symmetric(vertical: 5),
                  decoration: BoxDecoration(
                    color: Colors.lightBlueAccent.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(10)
                  ),
                  child: Row(
                    children: [
                      Image.network(
                        productModel?.products?[index]?.thumbnail??'',
                        width: 50,
                        height: 50,
                        fit: BoxFit.cover
                      ),
                      SizedBox(width: 10),
                      Text(productModel?.products?[index]?.title??''),
                      SizedBox(width: 10),
                      Text(productModel?.products?[index]?.price.toString()??''),
                    ]
                  )
                );
              }
            )
          )
        ]
      )
    );
  }
}