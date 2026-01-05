// models/credit_card_model.dart
class CreditCardModel {
  final String id;
  final String bankName;
  final String cardNumber;
  final int dueDate;
  final double spent;
  final double creditLimit;
  final int rewardPoints;
  final String cardHolderName;
  final String cardType; // Visa, Mastercard, Amex, etc.
  final String colorScheme; // Primary color for card UI
  final DateTime createdAt;
  final DateTime? expiryDate;
  final double minimumPayment;
  final double availableCredit;
  final List<Transaction> transactions;

  CreditCardModel({
    required this.id,
    required this.bankName,
    required this.cardNumber,
    required this.dueDate,
    this.spent = 0.0,
    this.creditLimit = 0.0,
    this.rewardPoints = 0,
    this.cardHolderName = '',
    this.cardType = 'Visa',
    this.colorScheme = 'blue',
    required this.createdAt,
    this.expiryDate,
    this.minimumPayment = 0.0,
    this.availableCredit = 0.0,
    this.transactions = const [],
  });

  double get utilizationPercentage {
    if (creditLimit == 0) return 0;
    return (spent / creditLimit) * 100;
  }

  double get remainingCredit => creditLimit - spent;

  Map<String, dynamic> toMap() {
    return {
      'bankName': bankName,
      'cardNumber': cardNumber,
      'dueDate': dueDate,
      'spent': spent,
      'creditLimit': creditLimit,
      'rewardPoints': rewardPoints,
      'cardHolderName': cardHolderName,
      'cardType': cardType,
      'colorScheme': colorScheme,
      'createdAt': createdAt.toIso8601String(),
      'expiryDate': expiryDate?.toIso8601String(),
      'minimumPayment': minimumPayment,
      'availableCredit': remainingCredit,
      'transactions': transactions.map((t) => t.toMap()).toList(),
    };
  }

  factory CreditCardModel.fromMap(String id, Map<String, dynamic> map) {
    // Handle numeric conversions safely
    double toDouble(dynamic value) {
      if (value == null) return 0.0;
      if (value is double) return value;
      if (value is int) return value.toDouble();
      if (value is String) return double.tryParse(value) ?? 0.0;
      return 0.0;
    }

    int toInt(dynamic value) {
      if (value == null) return 0;
      if (value is int) return value;
      if (value is double) return value.toInt();
      if (value is String) return int.tryParse(value) ?? 0;
      return 0;
    }

    return CreditCardModel(
      id: id,
      bankName: map['bankName']?.toString() ?? '',
      cardNumber: map['cardNumber']?.toString() ?? '',
      dueDate: toInt(map['dueDate']),
      spent: toDouble(map['spent']),
      creditLimit: toDouble(map['creditLimit']),
      rewardPoints: toInt(map['rewardPoints']),
      cardHolderName: map['cardHolderName']?.toString() ?? '',
      cardType: map['cardType']?.toString() ?? 'Visa',
      colorScheme: map['colorScheme']?.toString() ?? 'blue',
      createdAt: map['createdAt'] != null 
          ? DateTime.tryParse(map['createdAt'].toString()) ?? DateTime.now()
          : DateTime.now(),
      expiryDate: map['expiryDate'] != null 
          ? DateTime.tryParse(map['expiryDate'].toString())
          : null,
      minimumPayment: toDouble(map['minimumPayment']),
      transactions: (map['transactions'] as List?)
              ?.where((t) => t != null)
              .map((t) => Transaction.fromMap(t as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  CreditCardModel copyWith({
    String? id,
    String? bankName,
    String? cardNumber,
    int? dueDate,
    double? spent,
    double? creditLimit,
    int? rewardPoints,
    String? cardHolderName,
    String? cardType,
    String? colorScheme,
    DateTime? createdAt,
    DateTime? expiryDate,
    double? minimumPayment,
    List<Transaction>? transactions,
  }) {
    return CreditCardModel(
      id: id ?? this.id,
      bankName: bankName ?? this.bankName,
      cardNumber: cardNumber ?? this.cardNumber,
      dueDate: dueDate ?? this.dueDate,
      spent: spent ?? this.spent,
      creditLimit: creditLimit ?? this.creditLimit,
      rewardPoints: rewardPoints ?? this.rewardPoints,
      cardHolderName: cardHolderName ?? this.cardHolderName,
      cardType: cardType ?? this.cardType,
      colorScheme: colorScheme ?? this.colorScheme,
      createdAt: createdAt ?? this.createdAt,
      expiryDate: expiryDate ?? this.expiryDate,
      minimumPayment: minimumPayment ?? this.minimumPayment,
      transactions: transactions ?? this.transactions,
    );
  }
}

class Transaction {
  final String id;
  final double amount;
  final String description;
  final String category;
  final DateTime date;
  final String type; // 'debit' or 'credit'

  Transaction({
    required this.id,
    required this.amount,
    required this.description,
    required this.category,
    required this.date,
    this.type = 'debit',
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'amount': amount,
      'description': description,
      'category': category,
      'date': date.toIso8601String(),
      'type': type,
    };
  }

  factory Transaction.fromMap(Map<String, dynamic> map) {
    double toDouble(dynamic value) {
      if (value == null) return 0.0;
      if (value is double) return value;
      if (value is int) return value.toDouble();
      if (value is String) return double.tryParse(value) ?? 0.0;
      return 0.0;
    }

    return Transaction(
      id: map['id']?.toString() ?? '',
      amount: toDouble(map['amount']),
      description: map['description']?.toString() ?? '',
      category: map['category']?.toString() ?? 'Other',
      date: map['date'] != null 
          ? (DateTime.tryParse(map['date'].toString()) ?? DateTime.now())
          : DateTime.now(),
      type: map['type']?.toString() ?? 'debit',
    );
  }
}
