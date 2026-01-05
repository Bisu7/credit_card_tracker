import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../models/credit_card_model.dart';

class AddCardScreen extends StatefulWidget {
  final CreditCardModel? card;

  const AddCardScreen({super.key, this.card});

  @override
  State<AddCardScreen> createState() => _AddCardScreenState();
}

class _AddCardScreenState extends State<AddCardScreen> {
  final _formKey = GlobalKey<FormState>();
  final _bankController = TextEditingController();
  final _numberController = TextEditingController();
  final _holderController = TextEditingController();
  final _limitController = TextEditingController();
  final _dueController = TextEditingController();
  final _minimumPaymentController = TextEditingController();
  
  String _selectedCardType = 'Visa';
  String _selectedColor = 'blue';
  bool _loading = false;

  final List<String> _cardTypes = ['Visa', 'Mastercard', 'American Express', 'Discover'];
  final List<Map<String, dynamic>> _colors = [
    {'name': 'blue', 'color': const Color(0xFF3B82F6)},
    {'name': 'purple', 'color': const Color(0xFF8B5CF6)},
    {'name': 'pink', 'color': const Color(0xFFEC4899)},
    {'name': 'green', 'color': const Color(0xFF10B981)},
    {'name': 'orange', 'color': const Color(0xFFF59E0B)},
  ];

  @override
  void initState() {
    super.initState();
    if (widget.card != null) {
      _bankController.text = widget.card!.bankName;
      _numberController.text = widget.card!.cardNumber;
      _holderController.text = widget.card!.cardHolderName;
      _limitController.text = widget.card!.creditLimit.toStringAsFixed(0);
      _dueController.text = widget.card!.dueDate.toString();
      _minimumPaymentController.text = widget.card!.minimumPayment.toStringAsFixed(2);
      _selectedCardType = widget.card!.cardType;
      _selectedColor = widget.card!.colorScheme;
    }
  }

  @override
  void dispose() {
    _bankController.dispose();
    _numberController.dispose();
    _holderController.dispose();
    _limitController.dispose();
    _dueController.dispose();
    _minimumPaymentController.dispose();
    super.dispose();
  }

  String _formatCardNumber(String value) {
    final cleaned = value.replaceAll(RegExp(r'[^0-9]'), '');
    final buffer = StringBuffer();
    for (int i = 0; i < cleaned.length; i++) {
      if (i > 0 && i % 4 == 0) {
        buffer.write(' ');
      }
      buffer.write(cleaned[i]);
    }
    return buffer.toString();
  }

  Future<void> _saveCard() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      setState(() => _loading = true);

      final uid = FirebaseAuth.instance.currentUser!.uid;
      final cardNumber = _numberController.text.replaceAll(' ', '');
      
      final card = CreditCardModel(
        id: widget.card?.id ?? DateTime.now().millisecondsSinceEpoch.toString(),
        bankName: _bankController.text.trim(),
        cardNumber: cardNumber,
        dueDate: int.parse(_dueController.text),
        creditLimit: double.parse(_limitController.text),
        cardHolderName: _holderController.text.trim(),
        cardType: _selectedCardType,
        colorScheme: _selectedColor,
        createdAt: widget.card?.createdAt ?? DateTime.now(),
        minimumPayment: double.tryParse(_minimumPaymentController.text) ?? 0.0,
      );

      await FirebaseFirestore.instance
          .collection('users')
          .doc(uid)
          .collection('cards')
          .doc(card.id)
          .set(card.toMap());

      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(widget.card != null ? 'Card updated!' : 'Card added!'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.card != null ? 'Edit Card' : 'Add Credit Card'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Card Preview
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      _colors.firstWhere((c) => c['name'] == _selectedColor)['color'] as Color,
                      (_colors.firstWhere((c) => c['name'] == _selectedColor)['color'] as Color)
                          .withOpacity(0.7),
                    ],
                  ),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            _selectedCardType.toUpperCase(),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 40),
                    Text(
                      _numberController.text.isEmpty
                          ? '**** **** **** ****'
                          : _formatCardNumber(_numberController.text),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      _holderController.text.isEmpty
                          ? 'CARD HOLDER NAME'
                          : _holderController.text.toUpperCase(),
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        letterSpacing: 1,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),

              // Form Fields
              TextFormField(
                controller: _bankController,
                decoration: const InputDecoration(
                  labelText: 'Bank Name',
                  prefixIcon: Icon(Icons.account_balance),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter bank name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _numberController,
                decoration: const InputDecoration(
                  labelText: 'Card Number',
                  prefixIcon: Icon(Icons.credit_card),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(16),
                ],
                validator: (value) {
                  if (value == null || value.replaceAll(' ', '').length < 13) {
                    return 'Please enter a valid card number';
                  }
                  return null;
                },
                onChanged: (value) {
                  setState(() {
                    _numberController.value = TextEditingValue(
                      text: _formatCardNumber(value),
                      selection: _numberController.selection,
                    );
                  });
                },
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _holderController,
                decoration: const InputDecoration(
                  labelText: 'Card Holder Name',
                  prefixIcon: Icon(Icons.person),
                ),
                textCapitalization: TextCapitalization.words,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter card holder name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _limitController,
                decoration: const InputDecoration(
                  labelText: 'Credit Limit',
                  prefixIcon: Icon(Icons.attach_money),
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter credit limit';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _dueController,
                decoration: const InputDecoration(
                  labelText: 'Due Date (Day of Month)',
                  prefixIcon: Icon(Icons.calendar_today),
                  hintText: 'e.g., 15',
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(2),
                ],
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter due date';
                  }
                  final day = int.tryParse(value);
                  if (day == null || day < 1 || day > 31) {
                    return 'Please enter a valid day (1-31)';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _minimumPaymentController,
                decoration: const InputDecoration(
                  labelText: 'Minimum Payment',
                  prefixIcon: Icon(Icons.payment),
                  hintText: '0.00',
                ),
                keyboardType: TextInputType.numberWithOptions(decimal: true),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter minimum payment';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 24),

              // Card Type Selection
              const Text(
                'Card Type',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 12,
                children: _cardTypes.map((type) {
                  final isSelected = _selectedCardType == type;
                  return ChoiceChip(
                    label: Text(type),
                    selected: isSelected,
                    onSelected: (selected) {
                      setState(() => _selectedCardType = type);
                    },
                    selectedColor: const Color(0xFF6366F1),
                    labelStyle: TextStyle(
                      color: isSelected ? Colors.white : Colors.white70,
                      fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),

              // Color Selection
              const Text(
                'Card Color',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: _colors.map((colorData) {
                  final isSelected = _selectedColor == colorData['name'];
                  return GestureDetector(
                    onTap: () {
                      setState(() => _selectedColor = colorData['name'] as String);
                    },
                    child: Container(
                      width: 50,
                      height: 50,
                      margin: const EdgeInsets.only(right: 12),
                      decoration: BoxDecoration(
                        color: colorData['color'] as Color,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: isSelected ? Colors.white : Colors.transparent,
                          width: 3,
                        ),
                      ),
                      child: isSelected
                          ? const Icon(Icons.check, color: Colors.white, size: 24)
                          : null,
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 32),

              // Save Button
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: _loading ? null : _saveCard,
                  child: _loading
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : Text(
                          widget.card != null ? 'Update Card' : 'Add Card',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}