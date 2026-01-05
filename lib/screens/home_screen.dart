import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:shimmer/shimmer.dart';
import '../providers/card_provider.dart';
import '../providers/auth_provider.dart';
import 'add_card_screen.dart';
import 'analytics_screen.dart';
import 'card_detail_screen.dart';
import 'transactions_screen.dart';
import '../widgets/credit_card_widget.dart';
import '../widgets/stat_card.dart';
import '../models/credit_card_model.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    final cardsAsync = ref.watch(cardProvider);

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          // App Bar
          SliverAppBar(
            expandedHeight: 120,
            floating: false,
            pinned: true,
            elevation: 0,
            backgroundColor: const Color(0xFF0A0E27),
            flexibleSpace: FlexibleSpaceBar(
              title: Text(
                'Credit Tracker',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  shadows: [
                    Shadow(
                      color: Colors.black.withOpacity(0.3),
                      offset: const Offset(0, 2),
                      blurRadius: 4,
                    ),
                  ],
                ),
              ),
              centerTitle: false,
              titlePadding: const EdgeInsets.only(left: 24, bottom: 16),
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.bar_chart_rounded),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const AnalyticsScreen(),
                    ),
                  );
                },
              ),
              IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () async {
                  await ref.read(authProvider).signOut();
                },
              ),
            ],
          ),
          // Content
          SliverToBoxAdapter(
            child: cardsAsync.when(
              loading: () => _buildLoadingState(),
              error: (e, _) => _buildErrorState(e.toString()),
              data: (cards) {
                if (cards.isEmpty) {
                  return _buildEmptyState();
                }
                return _buildContent(cards);
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => const AddCardScreen(),
            ),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Add Card'),
        backgroundColor: const Color(0xFF6366F1),
      ),
    );
  }

  Widget _buildContent(List<CreditCardModel> cards) {
    final totalCredit = cards.fold<double>(0, (sum, card) => sum + card.creditLimit);
    final totalSpent = cards.fold<double>(0, (sum, card) => sum + card.spent);
    final totalAvailable = cards.fold<double>(0, (sum, card) => sum + card.remainingCredit);
    final totalRewards = cards.fold<int>(0, (sum, card) => sum + card.rewardPoints);
    final averageUtilization = cards.isEmpty
        ? 0.0
        : cards.fold<double>(0, (sum, card) => sum + card.utilizationPercentage) /
            cards.length;

    // Find upcoming due dates
    final now = DateTime.now();
    final upcomingCards = cards.where((card) {
      final daysUntilDue = card.dueDate - now.day;
      return daysUntilDue >= 0 && daysUntilDue <= 7;
    }).toList();
    upcomingCards.sort((a, b) => a.dueDate.compareTo(b.dueDate));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Statistics Section
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Overview',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 16),
              GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                childAspectRatio: 1.3,
                children: [
                  StatCard(
                    title: 'Total Credit',
                    value: NumberFormat.currency(symbol: '\$', decimalDigits: 0)
                        .format(totalCredit),
                    icon: Icons.credit_card,
                    color: const Color(0xFF6366F1),
                  ),
                  StatCard(
                    title: 'Total Spent',
                    value: NumberFormat.currency(symbol: '\$', decimalDigits: 0)
                        .format(totalSpent),
                    icon: Icons.shopping_bag,
                    color: const Color(0xFFEC4899),
                    subtitle: '${averageUtilization.toStringAsFixed(1)}% utilization',
                  ),
                  StatCard(
                    title: 'Available',
                    value: NumberFormat.currency(symbol: '\$', decimalDigits: 0)
                        .format(totalAvailable),
                    icon: Icons.account_balance_wallet,
                    color: const Color(0xFF10B981),
                  ),
                  StatCard(
                    title: 'Reward Points',
                    value: NumberFormat('#,###').format(totalRewards),
                    icon: Icons.stars,
                    color: const Color(0xFFF59E0B),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Upcoming Payments
        if (upcomingCards.isNotEmpty) ...[
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Upcoming Payments',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                TextButton(
                  onPressed: () {
                    // Navigate to all transactions
                  },
                  child: const Text('View All'),
                ),
              ],
            ),
          ),
          SizedBox(
            height: 100,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 20),
              itemCount: upcomingCards.length,
              itemBuilder: (context, index) {
                final card = upcomingCards[index];
                final daysUntilDue = card.dueDate - now.day;
                return Container(
                  width: 280,
                  margin: const EdgeInsets.only(right: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        const Color(0xFF1E1B4B),
                        const Color(0xFF312E81),
                      ],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: const Color(0xFF6366F1).withOpacity(0.3),
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFF6366F1).withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.calendar_today,
                          color: Color(0xFF6366F1),
                          size: 24,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              card.bankName,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Due in $daysUntilDue days',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.7),
                                fontSize: 12,
                              ),
                            ),
                            Text(
                              'Due Date: ${card.dueDate}',
                              style: TextStyle(
                                color: Colors.white.withOpacity(0.5),
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Text(
                        NumberFormat.currency(symbol: '\$', decimalDigits: 0)
                            .format(card.minimumPayment),
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 20),
        ],

        // Quick Actions
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Quick Actions',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: StatCardCompact(
                      title: 'Transactions',
                      value: 'View All',
                      icon: Icons.receipt_long,
                      color: const Color(0xFF6366F1),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const TransactionsScreen(),
                          ),
                        );
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: StatCardCompact(
                      title: 'Analytics',
                      value: 'See Insights',
                      icon: Icons.insights,
                      color: const Color(0xFF8B5CF6),
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const AnalyticsScreen(),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),

        // Credit Cards List
        Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'My Cards',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  Text(
                    '${cards.length} ${cards.length == 1 ? 'card' : 'cards'}',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              ...cards.map((card) => CreditCardWidget(
                    card: card,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => CardDetailScreen(card: card),
                        ),
                      );
                    },
                  )),
            ],
          ),
        ),
        const SizedBox(height: 100),
      ],
    );
  }

  Widget _buildLoadingState() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        children: List.generate(3, (index) => _buildShimmerCard()),
      ),
    );
  }

  Widget _buildShimmerCard() {
    return Shimmer.fromColors(
      baseColor: const Color(0xFF1E1B4B),
      highlightColor: const Color(0xFF312E81),
      child: Container(
        height: 220,
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
        ),
      ),
    );
  }

  Widget _buildErrorState(String error) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.red,
            ),
            const SizedBox(height: 16),
            Text(
              'Error loading cards',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 18,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: TextStyle(
                color: Colors.white.withOpacity(0.5),
                fontSize: 12,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Padding(
      padding: const EdgeInsets.all(40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(32),
            decoration: BoxDecoration(
              color: const Color(0xFF1E1B4B),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.credit_card_outlined,
              size: 64,
              color: Color(0xFF6366F1),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'No Credit Cards Yet',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Start tracking your credit cards\nby adding your first card',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              color: Colors.white.withOpacity(0.7),
            ),
          ),
          const SizedBox(height: 32),
          ElevatedButton.icon(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const AddCardScreen(),
                ),
              );
            },
            icon: const Icon(Icons.add),
            label: const Text('Add Your First Card'),
          ),
        ],
      ),
    );
  }
}