import '../vo/Product.dart';
import 'dart:core';

class ProductModel {
  List<Product>? products;
  int? total;
  int? skip;
  int? limit;

  ProductModel(
    {
      this.products,
      this.total,
      this.skip,
      this.limit
    }
  );

  ProductModel.fromJson(Map<String, dynamic> json) {
    if (json['products'] != null) {
      products = <Product>[];
      json['products'].forEach( (ele) => products!.add(new Product.fromJson(ele)));
    }
    total = json['total'];
    skip = json['skip'];
    limit = json['limit'];
  }
}