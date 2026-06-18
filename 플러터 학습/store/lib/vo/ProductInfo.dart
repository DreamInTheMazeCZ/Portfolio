class ProductInfo {

  int index;
  int? price;
  String? productName;
  String? imagePath;

  ProductInfo(
    {
      required this.index,
      this.price,
      this.productName,
      this.imagePath,
    }
  );

  void printProductInfo(){
    print(index);
    print(price);
    print(productName);
    print(imagePath);
  }
}