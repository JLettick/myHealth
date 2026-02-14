/**
 * Cardio performance chart (line chart for distance/duration/pace/HR over time).
 */

import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { CardioHistoryDataPoint, CardioMetric } from '../../types/analytics';
import { CARDIO_METRIC_LABELS } from '../../types/analytics';
import { EmptyAnalyticsState } from './EmptyAnalyticsState';
import { formatDistance, formatDuration, formatPace } from '../../types/workout';

interface CardioPerformanceChartProps {
  data: CardioHistoryDataPoint[];
  exerciseName: string;
}

const METRIC_COLORS: Record<CardioMetric, string> = {
  total_distance_meters: '#2563eb',
  total_duration_seconds: '#7c3aed',
  avg_pace_seconds_per_km: '#059669',
  avg_heart_rate: '#dc2626',
};

const METRICS: CardioMetric[] = [
  'total_distance_meters',
  'total_duration_seconds',
  'avg_pace_seconds_per_km',
  'avg_heart_rate',
];

function formatTooltipValue(value: number, metric: CardioMetric): string {
  switch (metric) {
    case 'total_distance_meters':
      return formatDistance(value);
    case 'total_duration_seconds':
      return formatDuration(value);
    case 'avg_pace_seconds_per_km':
      return formatPace(value);
    case 'avg_heart_rate':
      return `${value} bpm`;
    default:
      return String(value);
  }
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function CardioPerformanceChart({
  data,
  exerciseName,
}: CardioPerformanceChartProps): JSX.Element {
  const [activeMetric, setActiveMetric] = useState<CardioMetric>('total_distance_meters');

  if (data.length === 0) {
    return <EmptyAnalyticsState message={`No cardio data for ${exerciseName} in this period.`} />;
  }

  // For pace, invert Y axis (lower = faster = better)
  const isPaceMetric = activeMetric === 'avg_pace_seconds_per_km';

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
            {CARDIO_METRIC_LABELS[metric]}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDateLabel}
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
          />
          <YAxis
            tick={{ fontSize: 12 }}
            stroke="#9ca3af"
            reversed={isPaceMetric}
            tickFormatter={(value) => {
              if (activeMetric === 'avg_pace_seconds_per_km') {
                const mins = Math.floor(value / 60);
                const secs = value % 60;
                return `${mins}:${String(secs).padStart(2, '0')}`;
              }
              return String(value);
            }}
          />
          <Tooltip
            labelFormatter={(label) => formatDateLabel(label as string)}
            formatter={(value: number) => [
              formatTooltipValue(value, activeMetric),
              CARDIO_METRIC_LABELS[activeMetric],
            ]}
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
            }}
          />
          <Line
            type="monotone"
            dataKey={activeMetric}
            stroke={METRIC_COLORS[activeMetric]}
            strokeWidth={2}
            dot={{ r: 4, fill: METRIC_COLORS[activeMetric] }}
            activeDot={{ r: 6 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
