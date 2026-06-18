import 'package:flutter/material.dart';

class DetailPage extends StatefulWidget {
  
  final Map<String, dynamic> productMap;
  const DetailPage({super.key, required this.productMap});

  @override
  State<DetailPage> createState() => _DetailPage();
}

class _DetailPage extends State<DetailPage> {
  
  bool isClick = false;

  @override
  Widget build(BuildContext context) {

    return Scaffold(
      appBar: AppBar(title: Text(widget.productMap['productName'])),
      body: Column(
        children: [
          Stack(
            children: [
              Image.network(widget.productMap['imagePath'], width: double.maxFinite),
              Positioned(
                child: GestureDetector(
                  onTap: () {
                    setState( () {
                      isClick = isClick?false:true;
                    });
                  },
                  child: Icon(isClick?Icons.favorite:Icons.favorite_border)
                ),
                bottom: 15,
                left: 10,
              )
            ]
          ),
          SizedBox(height: 10,), 
          Text(widget.productMap['productName']),
          SizedBox(height: 10,), 
          Text(widget.productMap['price'].toString() + '원'),
        ]
      )
    );
  }  
}