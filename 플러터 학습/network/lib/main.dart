import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../pages/MainPage.dart';
import '../controller/DataController.dart';

void main() {

  // 컨트롤러 등록
  Get.put(DataController());
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: .fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MainPage(),
    );
  }
}