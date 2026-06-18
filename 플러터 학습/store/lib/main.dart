import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'package:store/pages/MainPage.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: '싱싱마을',
      theme: ThemeData(
        primarySwatch: Colors.lightBlue,
      ),
      home: MainPage()
    );
  }
}