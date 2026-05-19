-- Run this ONCE in Supabase SQL Editor before the first sync

create table if not exists nepse_daily_prices (
    id                       bigserial primary key,
    business_date            date          not null,
    security_id              int,
    symbol                   text          not null,
    security_name            text,
    open_price               numeric(10,2),
    high_price               numeric(10,2),
    low_price                numeric(10,2),
    close_price              numeric(10,2),
    total_traded_quantity    bigint,
    total_traded_value       numeric(18,2),
    total_trades             int,
    average_traded_price     numeric(10,2),
    previous_day_close_price numeric(10,2),
    last_updated_price       numeric(10,2),
    last_updated_time        timestamptz,
    fifty_two_week_high      numeric(10,2),
    fifty_two_week_low       numeric(10,2),
    market_capitalization    numeric(20,2),
    created_at               timestamptz   default now()
);

-- Unique constraint for upsert (no duplicate rows per stock per day)
alter table nepse_daily_prices
    add constraint if not exists uq_nepse_date_symbol unique (business_date, symbol);

-- Indexes
create index if not exists idx_nepse_date   on nepse_daily_prices (business_date desc);
create index if not exists idx_nepse_symbol on nepse_daily_prices (symbol);

-- Row Level Security
alter table nepse_daily_prices enable row level security;
create policy if not exists "Public read"    on nepse_daily_prices for select using (true);
create policy if not exists "Service insert" on nepse_daily_prices for insert with check (true);
create policy if not exists "Service update" on nepse_daily_prices for update using (true);
