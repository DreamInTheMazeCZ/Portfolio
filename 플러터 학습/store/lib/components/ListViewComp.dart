import 'package:flutter/material.dart';
import 'package:store/pages/DetailPage.dart';
import 'package:get/get.dart';

class ListViewComp extends StatelessWidget {

  final List<Map<String, dynamic>> productList;
  const ListViewComp({super.key, required this.productList});

  @override
  Widget build(BuildContext context) {
    
    return Expanded(

      child: ListView.builder(
        
        itemCount: productList.length,
        itemBuilder: (context, index) {
          
          return GestureDetector(
            onTap: () {
              Get.to( () => DetailPage(productMap: productList[index]) );
            },
            child: Column(
              children: [
                Container(
                  color: Colors.orange,
                  margin: EdgeInsets.all(15),
                  child: Row(
                    children: [
                      SizedBox(width: 10),

                      SizedBox(
                        width: 150,
                        height: 150,
                        child: ClipRRect(borderRadius: BorderRadiusGeometry.all(Radius.circular(10)),child: Image.network(productList[index]['imagePath']),),
                      ),
                      
                      SizedBox(width: 10),
                      Column(
                        children: [
                          Center(child: Text(productList[index]['productName'])),
                          Center(child: Text('${productList[index]['price']}원')),
                        ]
                      ),
                      SizedBox(width: 10),
                      SizedBox(width: 10),
                      SizedBox(width: 10),
                    ]
                  )
                ),
              ]
            )
          );
        }
      )       
    );
  }
}