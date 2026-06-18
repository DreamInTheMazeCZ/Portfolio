import 'package:get/get.dart';

import '../service/HttpService.dart';
import '../model/ProductModel.dart';

class DataController extends GetxController {

  final HttpService httpService = HttpService();

  ProductModel? productModel; // 데이터 모델

  Future<bool> getProductList() async {

    try {
      ProductModel info = await httpService.getProductList();
      productModel = info;
      update();
      return true;
      
    } catch (error) {
      print(error);
      return false;
    }
  }
}