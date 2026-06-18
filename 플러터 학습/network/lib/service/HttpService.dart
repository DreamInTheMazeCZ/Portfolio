import 'dart:convert';

import '../model/ProductModel.dart';
import '../vo/Product.dart';

import 'package:http/http.dart' as http;

class HttpService {

  // ProductList 호출 서비스
  Future<ProductModel> getProductList() async {
    String url = 'https://dummyjson.com/products';
    Uri uri = Uri.parse(url);

    final response = await http.get(uri);
    if (response.statusCode == 200) {
      return ProductModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Server Fail');
    }
  }

  Future<ProductModel> getProductOne(int id) async {
    String url = 'https://dummyjson.com/products/${id}';
    Uri uri = Uri.parse(url);

    final response = await http.get(uri);
    if (response.statusCode == 200) {
      return ProductModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Server Fail');
    }
  }
}