import 'package:flutter/material.dart';

class ProductDetailPage extends StatelessWidget {

  final String productName;
  final String imagePath;
  final String price;

  const ProductDetailPage({super.key ,required this.productName ,required this.imagePath, required this.price});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("$productName 상세페이지"),),
      body: SingleChildScrollView(
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 10),
          width: double.infinity,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(productName),
              SizedBox(height: 50,),
              Image.network(imagePath),
              SizedBox(height: 50,),
              Text(price),
              SizedBox(height: 20,),
              Text('구매자 목록'),
              Column(
                children: [
                  Container(
                    margin: EdgeInsets.symmetric(vertical: 4),
                    width: 100,
                    height: 30,
                    decoration: BoxDecoration(
                      color: Colors.lightBlueAccent,
                      border: Border.all(color: Colors.black)
                    ),
                    child: Center(child: Text('김철수'))
                  ),
                  Container(
                    margin: EdgeInsets.symmetric(vertical: 4),
                    width: 100,
                    height: 30,
                    decoration: BoxDecoration(
                      color: Colors.lightBlueAccent,
                      border: Border.all(color: Colors.black)
                    ),
                    child: Center(child: Text('김영희'))
                  ),
                  Container(
                    margin: EdgeInsets.symmetric(vertical: 4),
                    width: 100,
                    height: 30,
                    decoration: BoxDecoration(
                      color: Colors.lightBlueAccent,
                      border: Border.all(color: Colors.black)
                    ),
                    child: Center(child: Text('박상희'))
                  )
                ],
              )
            ],
          ),
        ),
      )
    );
  }
}