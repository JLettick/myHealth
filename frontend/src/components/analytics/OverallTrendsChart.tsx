/**
 * Overall trends chart (bar chart for weekly session count/volume/distance/duration).
 */

import { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { WeeklyTrendDataPoint, TrendsMetric } from '../../types/analytics';
import { TRENDS_METRIC_LABELS } from '../../types/analytics';
import { EmptyAnalyticsState } from './EmptyAnalyticsState';

interface OverallTrendsChartProps {
  data: WeeklyTrendDataPoint[];
  workoutsPerWeekTarget: number | null;
  minutesPerWeekTarget: number | null;
}

const METRIC_COLORS: Record<TrendsMetric, string> = {
  total_sessions: '#2563eb',
  total_sets: '#7c3aed',
  total_volume_kg: '#059669',
  total_distance_meters: '#d97706',
  total_duration_minutes: '#dc2626',
};

const METRICS: TrendsMetric[] = [
  'total_sessions',
  'total_sets',
  'total_volume_kg',
  'total_distance_meters',
  'total_duration_minutes',
];

function formatTooltipValue(value: number, metric: TrendsMetric): string {
  switch (metric) {
    case 'total_sessions':
      return `${value} sessions`;
    case 'total_sets':
      return `${value} sets`;
    case 'total_volume_kg':
      return `${Math.round(value).toLocaleString()} kg`;
    case 'total_distance_meters':
      return value >= 1000 ? `${(value / 1000).toFixed(1)} km` : `${Math.round(value)} m`;
    case 'total_duration_minutes':
      return `${Math.round(value)} min`;
    default:
      return String(value);
  }
}

function formatWeekLabel(weekStart: string): string {
  const d = new Date(weekStart + 'T12:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function OverallTrendsChart({
  data,
  workoutsPerWeekTarget,
  minutesPerWeekTarget,
}: OverallTrendsChartProps): JSX.Element {
  const [activeMetric, setActiveMetric] = useState<TrendsMetric>('total_sessions');

  if (data.length === 0) {
    return <EmptyAnalyticsState message="No workout data for this period." />;
  }

  // Show reference line for goals when applicable
  const goalValue =
    activeMetric === 'total_sessions'
      ? workoutsPerWeekTarget
      : activeMetric === 'total_duration_minutes'
        ? minutesPerWeekTarget
        : null;

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        {METRICS.map((metric) => (
          <button
            key={metric}
            onClick={() => setActiveMetric(metric)}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              activeMetric === metric
                ? 'text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            style={activeMetric === metric ? { backgroundColor: METRIC_COLORS[metric] } : undefined}
          >
            {TRENDS_METRIC_LABELS[metric]}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="week_start"
            tickFormatter={formatWeekLabel}
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <Tooltip
            labelFormatter={(label) => `Week of ${formatWeekLabel(label as string)}`}
            formatter={(value: number) => [
              formatTooltipValue(value, activeMetric),
              TRENDS_METRIC_LABELS[activeMetric],
            ]}
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
          />
          <Bar
            dataKey={activeMetric}
            fill={METRIC_COLORS[activeMetric]}
            radius={[4, 4, 0, 0]}
            maxBarSize={60}
          />
          {goalValue != null && (
            <ReferenceLine
              y={goalValue}
              stroke="#f59e0b"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{
                value: 'Goal',
                position: 'right',
                fill: '#f59e0b',
                fontSize: 12,
              }}
            />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
