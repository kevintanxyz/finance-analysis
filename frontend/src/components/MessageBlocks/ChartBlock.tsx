import {
  LineChart,
  Line,
  PieChart,
  Pie,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ChartBlock as ChartBlockType } from '../../types/messageBlocks';
import { cn } from '@/lib/utils';

interface ChartBlockProps {
  block: ChartBlockType;
}

// Default color palette
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export function ChartBlock({ block }: ChartBlockProps) {
  const { chartType, title, data, config } = block;

  if (!data || data.length === 0) {
    return (
      <div className="text-sm text-muted-foreground italic">No data available for chart</div>
    );
  }

  return (
    <div className={cn(
      "bg-card p-4 border border-border rounded-lg overflow-hidden",
      chartType === 'pie' ? "w-full" : ""
    )}>
      {title && (
        <h3 className="text-base font-semibold text-foreground mb-3">{title}</h3>
      )}

      <ResponsiveContainer width="100%" height={chartType === 'pie' ? 400 : 300} className={chartType === 'pie' ? 'sm:h-[400px]' : 'sm:h-[350px]'}>
        {chartType === 'line' && (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey={config?.xKey || 'date'}
              label={config?.xLabel ? {
                value: config.xLabel,
                position: 'insideBottom',
                offset: -5,
                style: { fontSize: '14px', fill: 'hsl(var(--foreground))', fontWeight: 600 }
              } : undefined}
              tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              stroke="hsl(var(--border))"
            />
            <YAxis
              label={config?.yLabel ? {
                value: config.yLabel,
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: '14px', fill: 'hsl(var(--foreground))', fontWeight: 600 }
              } : undefined}
              tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              stroke="hsl(var(--border))"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--popover))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem',
                fontSize: '12px',
                color: 'hsl(var(--popover-foreground))',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Line
              type="monotone"
              dataKey={config?.yKey || 'value'}
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={{ r: 4, fill: 'hsl(var(--primary))' }}
              activeDot={{ r: 6, fill: 'hsl(var(--primary))' }}
            />
          </LineChart>
        )}

        {chartType === 'pie' && (
          <PieChart>
            <Pie
              data={data}
              dataKey={config?.valueKey || 'value'}
              nameKey={config?.nameKey || 'name'}
              cx="50%"
              cy="45%"
              outerRadius={120}
              innerRadius={0}
              label={(entry) => `${entry.value}%`}
              labelLine={true}
              style={{ fontSize: '14px', fontWeight: 600 }}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color || config?.colors?.[index] || COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem',
                fontSize: '14px',
                color: '#000000',
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: '14px', paddingTop: '20px' }}
              iconSize={14}
              iconType="circle"
            />
          </PieChart>
        )}

        {chartType === 'bar' && (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey={config?.xKey || 'name'}
              label={config?.xLabel ? {
                value: config.xLabel,
                position: 'insideBottom',
                offset: -5,
                style: { fontSize: '14px', fill: 'hsl(var(--foreground))', fontWeight: 600 }
              } : undefined}
              tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              stroke="hsl(var(--border))"
            />
            <YAxis
              label={config?.yLabel ? {
                value: config.yLabel,
                angle: -90,
                position: 'insideLeft',
                style: { fontSize: '14px', fill: 'hsl(var(--foreground))', fontWeight: 600 }
              } : undefined}
              tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              stroke="hsl(var(--border))"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--popover))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem',
                fontSize: '12px',
                color: 'hsl(var(--popover-foreground))',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Bar
              dataKey={config?.yKey || 'value'}
              fill="hsl(var(--primary))"
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color || config?.colors?.[index] || COLORS[index % COLORS.length]}
                />
              ))}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
