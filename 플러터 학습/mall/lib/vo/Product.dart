class Product {

  String? productName;
  String? imagePath;
  String? price;

  Product({this.productName, this.imagePath, this.price});

  void printName(){
    print(productName);
  }
}