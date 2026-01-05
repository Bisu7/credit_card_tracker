import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../models/credit_card_model.dart' as model;

final cardProvider = StreamProvider<List<model.CreditCardModel>>((ref) {
  final user = FirebaseAuth.instance.currentUser;
  if (user == null) {
    return Stream.value([]);
  }

  return FirebaseFirestore.instance
      .collection('users')
      .doc(user.uid)
      .collection('cards')
      .snapshots()
      .map((snapshot) {
    return snapshot.docs.map((doc) {
      final data = doc.data();
      return model.CreditCardModel.fromMap(doc.id, data);
    }).toList();
  });
});

final cardServiceProvider = Provider((ref) => CardService());

class CardService {
  Future<void> addCard(model.CreditCardModel card) async {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    await FirebaseFirestore.instance
        .collection('users')
        .doc(uid)
        .collection('cards')
        .doc(card.id)
        .set(card.toMap());
  }

  Future<void> updateCard(model.CreditCardModel card) async {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    await FirebaseFirestore.instance
        .collection('users')
        .doc(uid)
        .collection('cards')
        .doc(card.id)
        .update(card.toMap());
  }

  Future<void> deleteCard(String cardId) async {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    await FirebaseFirestore.instance
        .collection('users')
        .doc(uid)
        .collection('cards')
        .doc(cardId)
        .delete();
  }

  Future<void> addTransaction(String cardId, model.Transaction transaction) async {
    final uid = FirebaseAuth.instance.currentUser!.uid;
    final cardDoc = await FirebaseFirestore.instance
        .collection('users')
        .doc(uid)
        .collection('cards')
        .doc(cardId)
        .get();

    if (cardDoc.exists) {
      final card = model.CreditCardModel.fromMap(cardId, cardDoc.data()!);
      final updatedTransactions = [...card.transactions, transaction];
      final newSpent = transaction.type == 'debit'
          ? card.spent + transaction.amount
          : card.spent - transaction.amount;

      await FirebaseFirestore.instance
          .collection('users')
          .doc(uid)
          .collection('cards')
          .doc(cardId)
          .update({
        'transactions': updatedTransactions.map((t) => t.toMap()).toList(),
        'spent': newSpent,
      });
    }
  }
}
