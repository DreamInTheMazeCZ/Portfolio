import 'package:flutter/material.dart';
import 'package:store/pages/DetailPage.dart';
import 'package:get/get.dart';

class GridViewComp extends StatelessWidget {

  final List<Map<String, dynamic>> productList;
  const GridViewComp({super.key, required this.productList});

  @override
  Widget build(BuildContext context) {
    
    return Expanded(
      child: GridView.builder(
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: 20,
          crossAxisSpacing: 15,
          childAspectRatio: 5/4,
        ),

        itemCount: productList.length,
        itemBuilder: (context, index) {
          
          return GestureDetector(
            onTap: () {
              Get.to(() => DetailPage(productMap: productList[index]));
            },
            child: Stack(
              alignment: Alignment.bottomCenter,
              children: [
                Center(child: Image.network(productList[index]['imagePath'])),            

                Positioned(
                  bottom: 50,
                  right: 15,
                  child: ClipRRect(
                    borderRadius: BorderRadiusGeometry.all(Radius.circular(5)),
                    child: Container(
                      height: 25,
                      color: Colors.red,
                      padding:EdgeInsets.all(2),
                      child: Center(child: Text(productList[index]['productName']))
                    ),
                  )
                ),

                Positioned(
                  bottom: 50,
                  left: 15,
                  child: ClipRRect(
                    borderRadius: BorderRadiusGeometry.all(Radius.circular(5)),
                    child: Container(
                      height: 25,
                      color: Colors.blue,
                      padding:EdgeInsets.all(2),
                      child: Center(child: Text('${productList[index]['price']}원'))
                    ),
                  )
                )
              ]
            )
          );
        },
      )
    );
  }
}