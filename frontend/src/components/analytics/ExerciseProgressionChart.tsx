/**
 * Exercise progression chart (line chart for weight/volume/reps/RPE over time).
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
import type { ExerciseHistoryDataPoint, ExerciseMetric } from '../../types/analytics';
import { EXERCISE_METRIC_LABELS } from '../../types/analytics';
import { EmptyAnalyticsState } from './EmptyAnalyticsState';
import { formatWeight } from '../../types/workout';

interface ExerciseProgressionChartProps {
  data: ExerciseHistoryDataPoint[];
  exerciseName: string;
}

const METRIC_COLORS: Record<ExerciseMetric, string> = {
  max_weight_kg: '#2563eb',
  total_volume_kg: '#7c3aed',
  total_reps: '#059669',
  avg_rpe: '#dc2626',
};

const METRICS: ExerciseMetric[] = ['max_weight_kg', 'total_volume_kg', 'total_reps', 'avg_rpe'];

function formatTooltipValue(value: number, metric: ExerciseMetric): string {
  switch (metric) {
    case 'max_weight_kg':
      return formatWeight(value);
    case 'total_volume_kg':
      return `${Math.round(value).toLocaleString()} kg`;
    case 'total_reps':
      return `${value} reps`;
    case 'avg_rpe':
      return `${value} RPE`;
    default:
      return String(value);
  }
}

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function ExerciseProgressionChart({
  data,
  exerciseName,
}: ExerciseProgressionChartProps): JSX.Element {
  const [activeMetric, setActiveMetric] = useState<ExerciseMetric>('max_weight_kg');

  if (data.length === 0) {
    return <EmptyAnalyticsState message={`No data for ${exerciseName} in this period.`} />;
  }

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
            {EXERCISE_METRIC_LABELS[metric]}
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
            domain={activeMetric === 'avg_rpe' ? [0, 10] : ['auto', 'auto']}
          />
          <Tooltip
            labelFormatter={(label) => formatDateLabel(label as string)}
            formatter={(value: number) => [
              formatTooltipValue(value, activeMetric),
              EXERCISE_METRIC_LABELS[activeMetric],
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
