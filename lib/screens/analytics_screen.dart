import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../providers/card_provider.dart';
import '../widgets/stat_card.dart';

class AnalyticsScreen extends ConsumerWidget {
  const AnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final cardsAsync = ref.watch(cardProvider);

    return Scaffold(
      body: cardsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text(e.toString())),
        data: (cards) {
          if (cards.isEmpty) {
            return const Center(
              child: Text('No data available'),
            );
          }

          final totalCredit = cards.fold<double>(0, (sum, card) => sum + card.creditLimit);
          final totalSpent = cards.fold<double>(0, (sum, card) => sum + card.spent);
          final totalAvailable = cards.fold<double>(0, (sum, card) => sum + card.remainingCredit);
          final averageUtilization =
              cards.fold<double>(0, (sum, card) => sum + card.utilizationPercentage) /
                  cards.length;

          // Category spending
          final categorySpending = <String, double>{};
          for (var card in cards) {
            for (var transaction in card.transactions) {
              if (transaction.type == 'debit') {
                categorySpending[transaction.category] =
                    (categorySpending[transaction.category] ?? 0) + transaction.amount;
              }
            }
          }

          return CustomScrollView(
            slivers: [
              SliverAppBar(
                expandedHeight: 100,
                floating: false,
                pinned: true,
                backgroundColor: const Color(0xFF0A0E27),
                flexibleSpace: const FlexibleSpaceBar(
                  title: Text('Analytics'),
                  centerTitle: false,
                  titlePadding: EdgeInsets.only(left: 24, bottom: 16),
                ),
              ),
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Summary Cards
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
                            title: 'Avg Utilization',
                            value: '${averageUtilization.toStringAsFixed(1)}%',
                            icon: Icons.trending_up,
                            color: const Color(0xFFF59E0B),
                          ),
                        ],
                      ),
                      const SizedBox(height: 32),

                      // Spending by Card Chart
                      const Text(
                        'Spending by Card',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 300,
                        child: Card(
                          color: const Color(0xFF1E1B4B),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: BarChart(
                              BarChartData(
                                alignment: BarChartAlignment.spaceAround,
                                maxY: totalCredit > 0 ? totalCredit + 1000 : 10000,
                                barTouchData: BarTouchData(
                                  touchTooltipData: BarTouchTooltipData(
                                    tooltipRoundedRadius: 8,
                                    tooltipBgColor: const Color(0xFF6366F1).withOpacity(0.8),
                                  ),
                                ),
                                titlesData: FlTitlesData(
                                  leftTitles: AxisTitles(
                                    sideTitles: SideTitles(
                                      showTitles: true,
                                      reservedSize: 40,
                                      getTitlesWidget: (value, meta) {
                                        return Text(
                                          '\$${(value / 1000).toStringAsFixed(0)}k',
                                          style: TextStyle(
                                            color: Colors.white.withOpacity(0.7),
                                            fontSize: 12,
                                          ),
                                        );
                                      },
                                    ),
                                  ),
                                  bottomTitles: AxisTitles(
                                    sideTitles: SideTitles(
                                      showTitles: true,
                                      getTitlesWidget: (value, meta) {
                                        if (value.toInt() >= cards.length) return const Text('');
                                        return Padding(
                                          padding: const EdgeInsets.only(top: 8),
                                          child: Text(
                                            cards[value.toInt()].bankName.length > 8
                                                ? '${cards[value.toInt()].bankName.substring(0, 8)}...'
                                                : cards[value.toInt()].bankName,
                                            style: TextStyle(
                                              color: Colors.white.withOpacity(0.7),
                                              fontSize: 10,
                                            ),
                                          ),
                                        );
                                      },
                                    ),
                                  ),
                                  topTitles: const AxisTitles(
                                    sideTitles: SideTitles(showTitles: false),
                                  ),
                                  rightTitles: const AxisTitles(
                                    sideTitles: SideTitles(showTitles: false),
                                  ),
                                ),
                                borderData: FlBorderData(show: false),
                                gridData: FlGridData(
                                  show: true,
                                  drawVerticalLine: false,
                                  getDrawingHorizontalLine: (value) {
                                    return FlLine(
                                      color: Colors.white.withOpacity(0.1),
                                      strokeWidth: 1,
                                    );
                                  },
                                ),
                                barGroups: List.generate(cards.length, (index) {
                                  final card = cards[index];
                                  return BarChartGroupData(
                                    x: index,
                                    barRods: [
                                      BarChartRodData(
                                        toY: card.spent,
                                        width: 20,
                                        borderRadius: const BorderRadius.vertical(
                                          top: Radius.circular(8),
                                        ),
                                        color: const Color(0xFF6366F1),
                                      ),
                                    ],
                                  );
                                }),
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 32),

                      // Category Spending
                      if (categorySpending.isNotEmpty) ...[
                        const Text(
                          'Spending by Category',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          height: 300,
                          child: Card(
                            color: const Color(0xFF1E1B4B),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: PieChart(
                                PieChartData(
                                  sectionsSpace: 2,
                                  centerSpaceRadius: 60,
                                  sections: categorySpending.entries.toList().asMap().entries.map((entry) {
                                    final index = entry.key;
                                    final categoryData = entry.value;
                                    final colors = [
                                      const Color(0xFF6366F1),
                                      const Color(0xFF8B5CF6),
                                      const Color(0xFFEC4899),
                                      const Color(0xFF10B981),
                                      const Color(0xFFF59E0B),
                                      const Color(0xFF06B6D4),
                                    ];
                                    final total = categorySpending.values.reduce((a, b) => a + b);
                                    final percentage = (categoryData.value / total * 100);

                                    return PieChartSectionData(
                                      value: categoryData.value,
                                      title: '${percentage.toStringAsFixed(0)}%',
                                      color: colors[index % colors.length],
                                      radius: 80,
                                      titleStyle: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.bold,
                                        color: Colors.white,
                                      ),
                                    );
                                  }).toList(),
                                ),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        ...categorySpending.entries.map((entry) {
                          final total = categorySpending.values.reduce((a, b) => a + b);
                          final percentage = (entry.value / total * 100);
                          return Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: const Color(0xFF1E1B4B),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 12,
                                  height: 12,
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF6366F1),
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(
                                    entry.key,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 14,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                ),
                                Text(
                                  NumberFormat.currency(symbol: '\$', decimalDigits: 0)
                                      .format(entry.value),
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.7),
                                    fontSize: 14,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  '${percentage.toStringAsFixed(1)}%',
                                  style: TextStyle(
                                    color: Colors.white.withOpacity(0.5),
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),
                      ],

                      const SizedBox(height: 32),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}