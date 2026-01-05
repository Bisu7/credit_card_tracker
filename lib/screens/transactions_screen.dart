import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../models/credit_card_model.dart';
import '../providers/card_provider.dart' as card_provider;

class TransactionsScreen extends ConsumerStatefulWidget {
  final String? cardId;

  const TransactionsScreen({super.key, this.cardId});

  @override
  ConsumerState<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends ConsumerState<TransactionsScreen> {
  final List<String> _categories = [
    'Food',
    'Shopping',
    'Transport',
    'Bills',
    'Entertainment',
    'Healthcare',
    'Travel',
    'Other',
  ];

  @override
  Widget build(BuildContext context) {
    final cardsAsync = ref.watch(card_provider.cardProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transactions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: () => _showAddTransactionDialog(context, ref),
          ),
        ],
      ),
      body: cardsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (cards) {
          List<Transaction> allTransactions = [];
          
          for (var card in cards) {
            if (widget.cardId == null || card.id == widget.cardId) {
              allTransactions.addAll(card.transactions);
            }
          }
          
          allTransactions.sort((a, b) => b.date.compareTo(a.date));

          if (allTransactions.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.receipt_long_outlined,
                    size: 64,
                    color: Colors.white.withOpacity(0.3),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'No transactions yet',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.5),
                      fontSize: 18,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: () => _showAddTransactionDialog(context, ref),
                    child: const Text('Add Transaction'),
                  ),
                ],
              ),
            );
          }

          // Group transactions by date
          final groupedTransactions = <String, List<Transaction>>{};
          for (var transaction in allTransactions) {
            final dateKey = DateFormat('yyyy-MM-dd').format(transaction.date);
            groupedTransactions.putIfAbsent(dateKey, () => []).add(transaction);
          }

          return ListView.builder(
            padding: const EdgeInsets.all(20),
            itemCount: groupedTransactions.length,
            itemBuilder: (context, index) {
              final dateKey = groupedTransactions.keys.toList()[index];
              final transactions = groupedTransactions[dateKey]!;
              final date = DateTime.parse(dateKey);
              final isToday = DateFormat('yyyy-MM-dd').format(DateTime.now()) == dateKey;
              final isYesterday = DateFormat('yyyy-MM-dd')
                      .format(DateTime.now().subtract(const Duration(days: 1))) ==
                  dateKey;

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: EdgeInsets.only(bottom: 12, top: index > 0 ? 24 : 0),
                    child: Text(
                      isToday
                          ? 'Today'
                          : isYesterday
                              ? 'Yesterday'
                              : DateFormat('MMM dd, yyyy').format(date),
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.7),
                        fontSize: 14,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  ...transactions.map((transaction) {
                    final card = cards.firstWhere(
                      (c) => c.transactions.any((t) => t.id == transaction.id),
                      orElse: () => cards.first,
                    );
                    return _buildTransactionTile(transaction, card);
                  }),
                ],
              );
            },
          );
        },
      ),
    );
  }

  Widget _buildTransactionTile(Transaction transaction, CreditCardModel card) {
    final isDebit = transaction.type == 'debit';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1E1B4B),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: (isDebit ? Colors.red : Colors.green).withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(
              _getCategoryIcon(transaction.category),
              color: isDebit ? Colors.red : Colors.green,
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  transaction.description,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        transaction.category,
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.7),
                          fontSize: 11,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      card.bankName,
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.5),
                        fontSize: 11,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      DateFormat('hh:mm a').format(transaction.date),
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.5),
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${isDebit ? '-' : '+'}${NumberFormat.currency(symbol: '\$').format(transaction.amount)}',
                style: TextStyle(
                  color: isDebit ? Colors.red : Colors.green,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'food':
        return Icons.restaurant;
      case 'shopping':
        return Icons.shopping_bag;
      case 'transport':
        return Icons.directions_car;
      case 'bills':
        return Icons.receipt;
      case 'entertainment':
        return Icons.movie;
      case 'healthcare':
        return Icons.medical_services;
      case 'travel':
        return Icons.flight;
      default:
        return Icons.category;
    }
  }

  void _showAddTransactionDialog(BuildContext context, WidgetRef ref) {
    final amountController = TextEditingController();
    final descriptionController = TextEditingController();
    String selectedCategory = 'Other';
    String selectedCardId = '';
    String transactionType = 'debit';

    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setState) {
            final cardsAsync = ref.watch(card_provider.cardProvider);
            return cardsAsync.when(
              loading: () => const AlertDialog(
                content: CircularProgressIndicator(),
              ),
              error: (e, _) => AlertDialog(
                content: Text(e.toString()),
              ),
              data: (cards) {
                if (selectedCardId.isEmpty && cards.isNotEmpty) {
                  selectedCardId = cards.first.id;
                }
                return AlertDialog(
                  backgroundColor: const Color(0xFF1E1B4B),
                  title: const Text('Add Transaction'),
                  content: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        TextField(
                          controller: descriptionController,
                          decoration: const InputDecoration(
                            labelText: 'Description',
                            prefixIcon: Icon(Icons.description),
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextField(
                          controller: amountController,
                          decoration: const InputDecoration(
                            labelText: 'Amount',
                            prefixIcon: Icon(Icons.attach_money),
                          ),
                          keyboardType: TextInputType.numberWithOptions(decimal: true),
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: transactionType,
                          decoration: const InputDecoration(
                            labelText: 'Type',
                            prefixIcon: Icon(Icons.swap_horiz),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'debit', child: Text('Debit (Expense)')),
                            DropdownMenuItem(value: 'credit', child: Text('Credit (Payment)')),
                          ],
                          onChanged: (value) {
                            setState(() => transactionType = value!);
                          },
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: selectedCategory,
                          decoration: const InputDecoration(
                            labelText: 'Category',
                            prefixIcon: Icon(Icons.category),
                          ),
                          items: _categories
                              .map((cat) => DropdownMenuItem(
                                    value: cat,
                                    child: Text(cat),
                                  ))
                              .toList(),
                          onChanged: (value) {
                            setState(() => selectedCategory = value!);
                          },
                        ),
                        const SizedBox(height: 16),
                        DropdownButtonFormField<String>(
                          value: selectedCardId.isEmpty ? null : selectedCardId,
                          decoration: const InputDecoration(
                            labelText: 'Card',
                            prefixIcon: Icon(Icons.credit_card),
                          ),
                          items: cards
                              .map((card) => DropdownMenuItem(
                                    value: card.id,
                                    child: Text(card.bankName),
                                  ))
                              .toList(),
                          onChanged: (value) {
                            setState(() => selectedCardId = value!);
                          },
                        ),
                      ],
                    ),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Cancel'),
                    ),
                    ElevatedButton(
                      onPressed: () async {
                        if (amountController.text.isEmpty ||
                            descriptionController.text.isEmpty ||
                            selectedCardId.isEmpty) {
                          return;
                        }

                        final transaction = Transaction(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          amount: double.parse(amountController.text),
                          description: descriptionController.text,
                          category: selectedCategory,
                          date: DateTime.now(),
                          type: transactionType,
                        );

                        await ref
                            .read(card_provider.cardServiceProvider)
                            .addTransaction(selectedCardId, transaction);

                        if (context.mounted) {
                          Navigator.pop(context);
                        }
                      },
                      child: const Text('Add'),
                    ),
                  ],
                );
              },
            );
          },
        );
      },
    );
  }
}
