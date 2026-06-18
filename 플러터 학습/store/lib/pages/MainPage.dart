import 'package:flutter/material.dart';

import 'package:store/components/GridViewComp.dart';
import 'package:store/components/ListViewComp.dart';

class MainPage extends StatefulWidget {
  const MainPage({super.key});

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {

  @override
  void initState() {

    isGridView = true;
    super.initState();

  }

  bool isGridView = true;

  final List<Map<String, dynamic>> productMap = [
    {
      'index': 0,
      'price': 3000,
      'productName': '포도',
      'imagePath': 'https://m.health.chosun.com/site/data/img_dir/2022/09/06/2022090602057_0.jpg',
    },
    {
      'index': 1,
      'price': 5000,
      'productName': '사과',
      'imagePath': 'https://cdn.imweb.me/thumbnail/20230107/6f41120888517.png',
    },
    {
      'index': 2,
      'price': 6000,
      'productName': '두부',
      'imagePath': 'https://m.health.chosun.com/site/data/img_dir/2023/03/29/2023032901669_0.jpg',
    },
    {
      'index': 3,
      'price': 7000,
      'productName': '어묵',
      'imagePath': 'https://m.health.chosun.com/site/data/img_dir/2023/02/16/2023021601045_0.jpg',
    },
    {
      'index': 4,
      'price': 8000,
      'productName': '고무장갑',
      'imagePath': 'https://imagescdn.gettyimagesbank.com/500/202012/a12155828.jpg',
    },
    {
      'index': 5,
      'price': 9000,
      'productName': '닭꼬치',
      'imagePath': 'https://sitem.ssgcdn.com/41/09/46/item/1000031460941_i2_750.jpg',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Center(child: Text('싱싱마을')),
        backgroundColor: Colors.lightGreen,
        toolbarHeight: 100,
      ),
      body: Column(
        children: [
          SizedBox(
            height: 50,
            child: Row(
              children: [
                SizedBox(
                  width: 20,
                ),

                GestureDetector(
                  onTap: () {
                    setState(() {
                      isGridView = true;
                      print(isGridView);
                    });
                  },
                  child: Container(
                    height: 30,
                    color: isGridView?Colors.blue:Colors.grey,
                    child: ClipRRect(
                      borderRadius: BorderRadiusGeometry.all(Radius.circular(10)),
                      child: Center(child: Text('그리드 뷰'),
                      )
                    )
                  ),
                ),                

                SizedBox(
                  width: 20,
                ),
                
                GestureDetector(
                  onTap: () {
                    setState(() {
                      isGridView = false;
                      print(isGridView);
                    });
                  },
                  child: Container(
                    height: 30,
                    color: isGridView?Colors.grey:Colors.blue,
                    child: ClipRRect(
                      borderRadius: BorderRadiusGeometry.all(Radius.circular(10)),
                      child: Center(child: Text('리스트 뷰'))
                    )
                  )
                )
              ]
            )
          ),
          
          if (isGridView)
          GridViewComp(productList: productMap),
          
          if (!isGridView)
          ListViewComp(productList: productMap)
        ]
      )
    );
  }
}