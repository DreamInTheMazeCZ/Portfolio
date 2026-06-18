import 'package:flutter/material.dart';

class MyPage extends StatefulWidget {

  final String name;
  final int ages;

  const MyPage({super.key, required this.name, required this.ages});

  @override
  State<MyPage> createState() => _MyPageState();
}

class _MyPageState extends State<MyPage> {

  @override
  void initState() {

    fullProfile = '${widget.name}${widget.ages}세';
    super.initState();

  }

  String fullProfile = '';
  int count = 0;
  bool over5 = false;

  void checkCount() {
    if (count < 5) {
      over5 = false;
    } else {
      over5 = true;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('$fullProfile 페이지')),
      body: GestureDetector(
        onTap: () {
          setState(() {
              count++;
              print(count);
            }
          );
          checkCount();
        },
        child: Center(
          child: Column(
            children: [
              if (over5)
              Text('count 5 이상일때만 나타남'),
              Text(fullProfile),
              Container(
                width: 100,
                height: 100,
                color: Colors.blue,
                child: Center(child: Text(count.toString()))
              )
            ],
          )          
        )
      )
    );
  }
}