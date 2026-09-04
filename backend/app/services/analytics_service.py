from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, desc, asc, text
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from backend.app.models.sales import SaleTransaction
from backend.app.schemas.analytics import (
    FilterParams, KPISummary, SalesTrendItem, ProfitTrendItem,
    CategoryPerformanceItem, SubCategoryPerformanceItem, ProductPerformanceItem,
    TopCustomerItem, CustomerPerformanceResponse, CustomerSegmentItem,
    RFMSegmentItem, GeographyItem, ShippingItem, DiscountImpactItem,
    OrderItem, PaginatedOrdersResponse, ReturnsResponse,
    DynamicInsightItem, DynamicInsightsResponse, FilterOptionsResponse
)

class AnalyticsService:
    """Enterprise-grade dynamic analytical calculation engine for E-Commerce Sales."""

    @staticmethod
    def _apply_filters(query, filters: FilterParams):
        """Apply all active multi-dimensional filter constraints to SQLAlchemy query."""
        if filters.year is not None:
            query = query.filter(SaleTransaction.year == filters.year)
        if filters.quarter is not None and filters.quarter != "all":
            query = query.filter(SaleTransaction.quarter == filters.quarter)
        if filters.month is not None:
            query = query.filter(SaleTransaction.month == filters.month)
        if filters.country and filters.country != "all":
            query = query.filter(SaleTransaction.country == filters.country)
        if filters.market and filters.market != "all":
            query = query.filter(SaleTransaction.market == filters.market)
        if filters.region and filters.region != "all":
            query = query.filter(SaleTransaction.region == filters.region)
        if filters.state and filters.state != "all":
            query = query.filter(SaleTransaction.state == filters.state)
        if filters.category and filters.category != "all":
            query = query.filter(SaleTransaction.category == filters.category)
        if filters.sub_category and filters.sub_category != "all":
            query = query.filter(SaleTransaction.sub_category == filters.sub_category)
        if filters.product_id and filters.product_id != "all":
            query = query.filter(SaleTransaction.product_id == filters.product_id)
        if filters.segment and filters.segment != "all":
            query = query.filter(SaleTransaction.segment == filters.segment)
        if filters.ship_mode and filters.ship_mode != "all":
            query = query.filter(SaleTransaction.ship_mode == filters.ship_mode)
        if filters.order_status and filters.order_status != "all":
            query = query.filter(SaleTransaction.order_status == filters.order_status)
        if filters.start_date:
            query = query.filter(SaleTransaction.order_date >= filters.start_date)
        if filters.end_date:
            query = query.filter(SaleTransaction.order_date <= filters.end_date)
        return query

    @classmethod
    def get_kpis(cls, db: Session, filters: FilterParams) -> KPISummary:
        """Compute top-level KPI metrics dynamically across the filtered slice."""
        q = db.query(
            func.sum(SaleTransaction.sales).label("total_revenue"),
            func.sum(SaleTransaction.profit).label("total_profit"),
            func.count(distinct(SaleTransaction.order_id)).label("total_orders"),
            func.sum(SaleTransaction.quantity).label("units_sold"),
            func.count(distinct(SaleTransaction.customer_id)).label("total_customers"),
            func.count(distinct(case((SaleTransaction.is_returned == True, SaleTransaction.order_id), else_=None))).label("returned_orders"),
            func.sum(case((SaleTransaction.is_returned == True, SaleTransaction.sales), else_=0.0)).label("returned_revenue"),
            func.count(distinct(case((SaleTransaction.profit > 0, SaleTransaction.order_id), else_=None))).label("profitable_orders"),
            func.count(distinct(case((SaleTransaction.profit <= 0, SaleTransaction.order_id), else_=None))).label("loss_orders"),
            func.avg(SaleTransaction.discount).label("avg_discount"),
            func.avg(SaleTransaction.shipping_cost).label("avg_shipping_cost")
        )
        q = cls._apply_filters(q, filters)
        row = q.one()

        revenue = float(row.total_revenue or 0.0)
        profit = float(row.total_profit or 0.0)
        orders = int(row.total_orders or 0)
        units = int(row.units_sold or 0)
        customers = int(row.total_customers or 0)
        returned_orders = int(row.returned_orders or 0)
        returned_rev = float(row.returned_revenue or 0.0)
        prof_orders = int(row.profitable_orders or 0)
        loss_orders = int(row.loss_orders or 0)

        margin = round((profit / revenue * 100), 2) if revenue > 0 else 0.0
        aov = round((revenue / orders), 2) if orders > 0 else 0.0
        return_rate = round((returned_orders / orders * 100), 2) if orders > 0 else 0.0
        avg_disc = round(float(row.avg_discount or 0.0) * 100, 2)
        avg_ship = round(float(row.avg_shipping_cost or 0.0), 2)

        return KPISummary(
            total_revenue=round(revenue, 2),
            total_profit=round(profit, 2),
            profit_margin=margin,
            total_orders=orders,
            units_sold=units,
            total_customers=customers,
            avg_order_value=aov,
            total_returned_orders=returned_orders,
            return_rate=return_rate,
            returned_revenue=round(returned_rev, 2),
            profitable_orders=prof_orders,
            loss_orders=loss_orders,
            avg_discount=avg_disc,
            avg_shipping_cost=avg_ship,
            total_sales=round(revenue, 2),
            total_quantity=units
        )

    @classmethod
    def get_sales_trend(cls, db: Session, filters: FilterParams) -> List[SalesTrendItem]:
        """Compute monthly sales revenue, order volumes, YoY growth, rolling and running totals."""
        q = db.query(
            SaleTransaction.year_month,
            SaleTransaction.year,
            SaleTransaction.month,
            SaleTransaction.month_name,
            SaleTransaction.quarter,
            func.sum(SaleTransaction.sales).label("revenue"),
            func.count(distinct(SaleTransaction.order_id)).label("orders"),
            func.sum(SaleTransaction.quantity).label("units")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(
            SaleTransaction.year_month,
            SaleTransaction.year,
            SaleTransaction.month,
            SaleTransaction.month_name,
            SaleTransaction.quarter
        ).order_by(SaleTransaction.year_month.asc())
        rows = q.all()

        if not rows:
            return []

        df = pd.DataFrame([{
            "period": r.year_month,
            "year": r.year,
            "month": r.month,
            "month_name": r.month_name,
            "quarter": r.quarter,
            "revenue": round(float(r.revenue), 2),
            "orders": int(r.orders),
            "units": int(r.units)
        } for r in rows])

        # Rolling 3-month revenue
        df["rolling_3m_revenue"] = df["revenue"].rolling(window=3, min_periods=1).mean().round(2)
        # Cumulative running total revenue
        df["running_total_revenue"] = df["revenue"].cumsum().round(2)

        # Year-over-Year growth calculation
        revenue_map = {(row["year"], row["month"]): row["revenue"] for _, row in df.iterrows()}
        yoy_growth_list = []
        for _, row in df.iterrows():
            prev_rev = revenue_map.get((row["year"] - 1, row["month"]))
            if prev_rev and prev_rev > 0:
                growth = round(((row["revenue"] - prev_rev) / prev_rev) * 100, 2)
            else:
                growth = None
            yoy_growth_list.append(growth)
        df["yoy_growth"] = yoy_growth_list

        results = []
        for _, row in df.iterrows():
            results.append(SalesTrendItem(
                period=row["period"],
                year=int(row["year"]),
                month=int(row["month"]),
                month_name=row["month_name"] or "",
                quarter=row["quarter"] or "",
                revenue=row["revenue"],
                orders=int(row["orders"]),
                units=int(row["units"]),
                yoy_growth=row["yoy_growth"],
                rolling_3m_revenue=row["rolling_3m_revenue"],
                running_total_revenue=row["running_total_revenue"],
                sales=row["revenue"],
                sales_mom_growth=None,
                sales_yoy_growth=row["yoy_growth"]
            ))
        return results

    @classmethod
    def get_profit_trend(cls, db: Session, filters: FilterParams) -> List[ProfitTrendItem]:
        """Compute monthly profit trajectory and profitable vs loss-making order distributions."""
        q = db.query(
            SaleTransaction.year_month,
            SaleTransaction.year,
            SaleTransaction.month,
            SaleTransaction.month_name,
            func.sum(SaleTransaction.profit).label("profit"),
            func.sum(SaleTransaction.sales).label("sales"),
            func.count(distinct(case((SaleTransaction.profit > 0, SaleTransaction.order_id), else_=None))).label("profitable_orders"),
            func.count(distinct(case((SaleTransaction.profit <= 0, SaleTransaction.order_id), else_=None))).label("loss_making_orders")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(
            SaleTransaction.year_month,
            SaleTransaction.year,
            SaleTransaction.month,
            SaleTransaction.month_name
        ).order_by(SaleTransaction.year_month.asc())
        rows = q.all()

        results = []
        for r in rows:
            p = round(float(r.profit or 0.0), 2)
            s = float(r.sales or 0.0)
            margin = round((p / s * 100), 2) if s > 0 else 0.0
            results.append(ProfitTrendItem(
                period=r.year_month,
                year=r.year,
                month=r.month,
                month_name=r.month_name or "",
                profit=p,
                profit_margin=margin,
                profitable_orders=int(r.profitable_orders or 0),
                loss_making_orders=int(r.loss_making_orders or 0)
            ))
        return results

    @classmethod
    def get_category_performance(cls, db: Session, filters: FilterParams) -> List[CategoryPerformanceItem]:
        """Compute category revenue, profit, margin, and overall contribution share."""
        q = db.query(
            SaleTransaction.category,
            func.sum(SaleTransaction.sales).label("revenue"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders"),
            func.sum(SaleTransaction.quantity).label("quantity")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(SaleTransaction.category).order_by(desc("revenue"))
        rows = q.all()

        total_rev = sum(float(r.revenue or 0.0) for r in rows)
        results = []
        for r in rows:
            rev = round(float(r.revenue or 0.0), 2)
            prof = round(float(r.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            share = round((rev / total_rev * 100), 2) if total_rev > 0 else 0.0
            results.append(CategoryPerformanceItem(
                category=r.category,
                revenue=rev,
                profit=prof,
                profit_margin=margin,
                orders=int(r.orders or 0),
                quantity=int(r.quantity or 0),
                share_of_total=share,
                sales=rev
            ))
        return results

    @classmethod
    def get_subcategory_performance(cls, db: Session, filters: FilterParams) -> List[SubCategoryPerformanceItem]:
        """Compute subcategory performance with share of parent category."""
        q = db.query(
            SaleTransaction.sub_category,
            SaleTransaction.category,
            func.sum(SaleTransaction.sales).label("revenue"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders"),
            func.sum(SaleTransaction.quantity).label("quantity")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(SaleTransaction.sub_category, SaleTransaction.category).order_by(desc("revenue"))
        rows = q.all()

        # Category totals for share calculation
        cat_totals = {}
        for r in rows:
            cat_totals[r.category] = cat_totals.get(r.category, 0.0) + float(r.revenue or 0.0)

        results = []
        for r in rows:
            rev = round(float(r.revenue or 0.0), 2)
            prof = round(float(r.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            cat_tot = cat_totals.get(r.category, 1.0)
            share = round((rev / cat_tot * 100), 2) if cat_tot > 0 else 0.0
            results.append(SubCategoryPerformanceItem(
                sub_category=r.sub_category,
                category=r.category,
                revenue=rev,
                profit=prof,
                profit_margin=margin,
                orders=int(r.orders or 0),
                quantity=int(r.quantity or 0),
                share_of_category=share,
                sales=rev
            ))
        return results

    @classmethod
    def get_top_products(cls, db: Session, filters: FilterParams, sort_by: str = "revenue", limit: int = 10) -> List[ProductPerformanceItem]:
        """Fetch top products ranked by revenue, profit, or units sold."""
        q = db.query(
            SaleTransaction.product_id,
            SaleTransaction.product_name,
            SaleTransaction.category,
            SaleTransaction.sub_category,
            func.sum(SaleTransaction.sales).label("revenue"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.sum(SaleTransaction.quantity).label("quantity"),
            func.avg(SaleTransaction.discount).label("avg_discount")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(
            SaleTransaction.product_id,
            SaleTransaction.product_name,
            SaleTransaction.category,
            SaleTransaction.sub_category
        )

        if sort_by == "profit":
            q = q.order_by(desc("profit"))
        elif sort_by == "quantity":
            q = q.order_by(desc("quantity"))
        else:
            q = q.order_by(desc("revenue"))

        rows = q.limit(limit).all()
        results = []
        for r in rows:
            rev = round(float(r.revenue or 0.0), 2)
            prof = round(float(r.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            disc = round(float(r.avg_discount or 0.0) * 100, 2)
            results.append(ProductPerformanceItem(
                product_id=r.product_id,
                product_name=r.product_name,
                category=r.category,
                sub_category=r.sub_category,
                revenue=rev,
                profit=prof,
                quantity=int(r.quantity or 0),
                profit_margin=margin,
                avg_discount=disc,
                sales=rev
            ))
        return results

    @classmethod
    def get_loss_making_products(cls, db: Session, filters: FilterParams, limit: int = 10) -> List[ProductPerformanceItem]:
        """Fetch bottom products with the largest negative profits (loss makers)."""
        q = db.query(
            SaleTransaction.product_id,
            SaleTransaction.product_name,
            SaleTransaction.category,
            SaleTransaction.sub_category,
            func.sum(SaleTransaction.sales).label("revenue"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.sum(SaleTransaction.quantity).label("quantity"),
            func.avg(SaleTransaction.discount).label("avg_discount")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(
            SaleTransaction.product_id,
            SaleTransaction.product_name,
            SaleTransaction.category,
            SaleTransaction.sub_category
        ).filter(SaleTransaction.profit < 0).order_by(asc("profit")).limit(limit)

        rows = q.all()
        results = []
        for r in rows:
            rev = round(float(r.revenue or 0.0), 2)
            prof = round(float(r.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            disc = round(float(r.avg_discount or 0.0) * 100, 2)
            results.append(ProductPerformanceItem(
                product_id=r.product_id,
                product_name=r.product_name,
                category=r.category,
                sub_category=r.sub_category,
                revenue=rev,
                profit=prof,
                quantity=int(r.quantity or 0),
                profit_margin=margin,
                avg_discount=disc,
                sales=rev
            ))
        return results

    @classmethod
    def get_customer_performance(cls, db: Session, filters: FilterParams) -> CustomerPerformanceResponse:
        """Compute customer metrics, repeat buyer rates, and top customer leaderboard."""
        q_base = db.query(
            SaleTransaction.customer_id,
            SaleTransaction.customer_name,
            SaleTransaction.segment,
            SaleTransaction.country,
            func.count(distinct(SaleTransaction.order_id)).label("order_count"),
            func.sum(SaleTransaction.sales).label("total_spend"),
            func.sum(SaleTransaction.profit).label("total_profit")
        )
        q_base = cls._apply_filters(q_base, filters)
        q_base = q_base.group_by(
            SaleTransaction.customer_id,
            SaleTransaction.customer_name,
            SaleTransaction.segment,
            SaleTransaction.country
        )
        cust_rows = q_base.all()

        total_customers = len(cust_rows)
        if total_customers == 0:
            return CustomerPerformanceResponse(
                total_customers=0,
                repeat_customers=0,
                single_purchase_customers=0,
                repeat_customer_rate=0.0,
                avg_revenue_per_customer=0.0,
                customer_contribution_top20=0.0,
                top_customers=[]
            )

        repeat_cust = sum(1 for r in cust_rows if r.order_count > 1)
        single_cust = total_customers - repeat_cust
        repeat_rate = round((repeat_cust / total_customers * 100), 2)

        total_rev = sum(float(r.total_spend or 0.0) for r in cust_rows)
        avg_rev = round(total_rev / total_customers, 2)

        # Sort for top customers and Pareto
        sorted_cust = sorted(cust_rows, key=lambda x: float(x.total_spend or 0.0), reverse=True)
        top20_count = max(1, int(total_customers * 0.2))
        top20_rev = sum(float(r.total_spend or 0.0) for r in sorted_cust[:top20_count])
        pareto = round((top20_rev / total_rev * 100), 2) if total_rev > 0 else 0.0

        top_customers = []
        for r in sorted_cust[:10]:
            spend = round(float(r.total_spend or 0.0), 2)
            orders = int(r.order_count or 0)
            aov = round(spend / orders, 2) if orders > 0 else 0.0
            top_customers.append(TopCustomerItem(
                customer_id=r.customer_id,
                customer_name=r.customer_name,
                segment=r.segment,
                country=r.country,
                total_spend=spend,
                total_profit=round(float(r.total_profit or 0.0), 2),
                order_count=orders,
                avg_order_value=aov
            ))

        return CustomerPerformanceResponse(
            total_customers=total_customers,
            repeat_customers=repeat_cust,
            single_purchase_customers=single_cust,
            repeat_customer_rate=repeat_rate,
            avg_revenue_per_customer=avg_rev,
            customer_contribution_top20=pareto,
            top_customers=top_customers
        )

    @classmethod
    def get_customer_segments(cls, db: Session, filters: FilterParams) -> List[CustomerSegmentItem]:
        """Compute segment revenue, profit, margin, and order metrics."""
        q = db.query(
            SaleTransaction.segment,
            func.count(distinct(SaleTransaction.customer_id)).label("customer_count"),
            func.sum(SaleTransaction.sales).label("revenue"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders_count")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(SaleTransaction.segment).order_by(desc("revenue"))
        rows = q.all()

        total_rev = sum(float(r.revenue or 0.0) for r in rows)
        results = []
        for r in rows:
            rev = round(float(r.revenue or 0.0), 2)
            prof = round(float(r.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            custs = int(r.customer_count or 0)
            avg_spend = round((rev / custs), 2) if custs > 0 else 0.0
            share = round((rev / total_rev * 100), 2) if total_rev > 0 else 0.0
            results.append(CustomerSegmentItem(
                segment=r.segment,
                customer_count=custs,
                revenue=rev,
                profit=prof,
                profit_margin=margin,
                orders_count=int(r.orders_count or 0),
                avg_spend=avg_spend,
                share_of_revenue=share,
                sales=rev
            ))
        return results

    @classmethod
    def get_rfm_analysis(cls, db: Session, filters: FilterParams) -> List[RFMSegmentItem]:
        """Compute dynamic Recency, Frequency, Monetary quartile scoring within current filter context."""
        # Find reference max date within the filtered context
        ref_q = db.query(func.max(SaleTransaction.order_date))
        ref_q = cls._apply_filters(ref_q, filters)
        max_date = ref_q.scalar()

        if not max_date:
            return []

        q = db.query(
            SaleTransaction.customer_id,
            func.max(SaleTransaction.order_date).label("last_order"),
            func.count(distinct(SaleTransaction.order_id)).label("frequency"),
            func.sum(SaleTransaction.sales).label("monetary"),
            func.sum(SaleTransaction.profit).label("profit")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(SaleTransaction.customer_id)
        rows = q.all()

        if len(rows) < 4:
            return []

        data = []
        for r in rows:
            recency = (max_date - r.last_order).days
            data.append({
                "customer_id": r.customer_id,
                "recency": max(0, recency),
                "frequency": int(r.frequency),
                "monetary": float(r.monetary),
                "profit": float(r.profit)
            })

        df = pd.DataFrame(data)

        # Quantile scoring (1-4)
        df["r_score"] = pd.qcut(df["recency"].rank(method="first"), q=4, labels=[4, 3, 2, 1]).astype(int)
        df["f_score"] = pd.qcut(df["frequency"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
        df["m_score"] = pd.qcut(df["monetary"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
        df["rfm_score"] = (df["r_score"] * 100) + (df["f_score"] * 10) + df["m_score"]

        # Behavioral Segment Mapping
        def assign_segment(row):
            r, f, m = row["r_score"], row["f_score"], row["m_score"]
            if r >= 3 and f >= 3:
                return "Champions"
            elif r >= 3 and f >= 2:
                return "Loyal Customers"
            elif r >= 3 and f == 1:
                return "Potential Loyalists"
            elif r == 2 and f >= 2:
                return "At Risk"
            elif r == 1 and f >= 3:
                return "Cannot Lose Them"
            else:
                return "Hibernating"

        df["segment"] = df.apply(assign_segment, axis=1)

        total_customers = len(df)
        results = []
        for seg_name, group in df.groupby("segment"):
            cust_count = len(group)
            results.append(RFMSegmentItem(
                segment=seg_name,
                customer_count=cust_count,
                total_revenue=round(float(group["monetary"].sum()), 2),
                total_profit=round(float(group["profit"].sum()), 2),
                avg_recency_days=round(float(group["recency"].mean()), 1),
                avg_frequency=round(float(group["frequency"].mean()), 1),
                avg_monetary=round(float(group["monetary"].mean()), 2),
                share_of_customers=round((cust_count / total_customers * 100), 2)
            ))

        results = sorted(results, key=lambda x: x.total_revenue, reverse=True)
        return results

    @classmethod
    def get_geography_analysis(cls, db: Session, filters: FilterParams, limit: int = 15) -> List[GeographyItem]:
        """Compute country, market, and regional sales and profitability."""
        q = db.query(
            SaleTransaction.country,
            SaleTransaction.market,
            SaleTransaction.region,
            func.sum(SaleTransaction.sales).label("revenue"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(SaleTransaction.country, SaleTransaction.market, SaleTransaction.region).order_by(desc("revenue")).limit(limit)
        rows = q.all()

        results = []
        for r in rows:
            rev = round(float(r.revenue or 0.0), 2)
            prof = round(float(r.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            results.append(GeographyItem(
                country=r.country,
                market=r.market or "Global",
                region=r.region,
                revenue=rev,
                profit=prof,
                profit_margin=margin,
                orders=int(r.orders or 0),
                sales=rev
            ))
        return results

    @classmethod
    def get_shipping_analysis(cls, db: Session, filters: FilterParams) -> List[ShippingItem]:
        """Compute volume, revenue, profit, and logistics costs across shipping modes."""
        q = db.query(
            SaleTransaction.ship_mode,
            func.count(distinct(SaleTransaction.order_id)).label("order_count"),
            func.sum(SaleTransaction.sales).label("total_revenue"),
            func.sum(SaleTransaction.profit).label("total_profit"),
            func.avg(SaleTransaction.shipping_cost).label("avg_shipping_cost"),
            func.avg(SaleTransaction.shipping_days).label("avg_shipping_days")
        )
        q = cls._apply_filters(q, filters)
        q = q.group_by(SaleTransaction.ship_mode).order_by(desc("total_revenue"))
        rows = q.all()

        results = []
        for r in rows:
            results.append(ShippingItem(
                ship_mode=r.ship_mode or "Standard",
                order_count=int(r.order_count or 0),
                total_revenue=round(float(r.total_revenue or 0.0), 2),
                total_profit=round(float(r.total_profit or 0.0), 2),
                avg_shipping_cost=round(float(r.avg_shipping_cost or 0.0), 2),
                avg_shipping_days=round(float(r.avg_shipping_days or 0.0), 1),
                sales=round(float(r.total_revenue or 0.0), 2)
            ))
        return results

    @classmethod
    def get_discount_impact(cls, db: Session, filters: FilterParams) -> List[DiscountImpactItem]:
        """Analyze revenue and profit margin impact across standardized discount bands."""
        bands = [
            ("No Discount (0%)", 0.0, 0.0),
            ("Low (1% - 10%)", 0.001, 0.10),
            ("Moderate (11% - 20%)", 0.101, 0.20),
            ("High (21% - 30%)", 0.201, 0.30),
            ("Aggressive (31% - 50%)", 0.301, 0.50),
            ("Severe (> 50%)", 0.501, 1.00)
        ]

        results = []
        for label, min_d, max_d in bands:
            q = db.query(
                func.count(distinct(SaleTransaction.order_id)).label("orders"),
                func.sum(SaleTransaction.sales).label("revenue"),
                func.sum(SaleTransaction.profit).label("profit"),
                func.count(distinct(case((SaleTransaction.profit < 0, SaleTransaction.order_id), else_=None))).label("loss_orders")
            )
            q = cls._apply_filters(q, filters)
            q = q.filter(SaleTransaction.discount >= min_d, SaleTransaction.discount <= max_d)
            row = q.one()

            rev = round(float(row.revenue or 0.0), 2)
            prof = round(float(row.profit or 0.0), 2)
            margin = round((prof / rev * 100), 2) if rev > 0 else 0.0
            results.append(DiscountImpactItem(
                discount_band=label,
                min_discount=min_d,
                max_discount=max_d,
                order_count=int(row.orders or 0),
                revenue=rev,
                profit=prof,
                profit_margin=margin,
                loss_orders_count=int(row.loss_orders or 0),
                sales=rev
            ))
        return results

    @classmethod
    def get_orders_paginated(
        cls, db: Session, filters: FilterParams,
        page: int = 1, page_size: int = 20, search: Optional[str] = None,
        sort_by: str = "order_date", sort_desc: bool = True
    ) -> PaginatedOrdersResponse:
        """Fetch server-side paginated, searchable, and sortable transaction records."""
        q = db.query(SaleTransaction)
        q = cls._apply_filters(q, filters)

        if search and search.strip():
            term = f"%{search.strip()}%"
            q = q.filter(
                (SaleTransaction.order_id.ilike(term)) |
                (SaleTransaction.customer_name.ilike(term)) |
                (SaleTransaction.product_name.ilike(term)) |
                (SaleTransaction.country.ilike(term))
            )

        total_records = q.count()
        total_pages = max(1, (total_records + page_size - 1) // page_size)

        # Dynamic column sort
        col_map = {
            "order_date": SaleTransaction.order_date,
            "sales": SaleTransaction.sales,
            "profit": SaleTransaction.profit,
            "quantity": SaleTransaction.quantity,
            "customer_name": SaleTransaction.customer_name,
            "country": SaleTransaction.country
        }
        sort_col = col_map.get(sort_by, SaleTransaction.order_date)
        if sort_desc:
            q = q.order_by(sort_col.desc())
        else:
            q = q.order_by(sort_col.asc())

        offset = (page - 1) * page_size
        records = q.offset(offset).limit(page_size).all()

        data = []
        for r in records:
            data.append(OrderItem(
                row_id=r.row_id or r.id,
                order_id=r.order_id,
                order_date=str(r.order_date),
                ship_date=str(r.ship_date) if r.ship_date else None,
                customer_name=r.customer_name,
                country=r.country,
                region=r.region,
                product_name=r.product_name,
                category=r.category,
                sub_category=r.sub_category,
                quantity=r.quantity,
                unit_price=r.unit_price,
                sales=r.sales,
                discount=r.discount,
                profit=r.profit,
                order_status=r.order_status,
                ship_mode=r.ship_mode or "Standard"
            ))

        return PaginatedOrdersResponse(
            total_records=total_records,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            data=data
        )

    @classmethod
    def get_returns_analysis(cls, db: Session, filters: FilterParams) -> ReturnsResponse:
        """Compute return volume, return rate %, returned revenue, and top returned products/customers."""
        kpis = cls.get_kpis(db, filters)

        # Top returned products
        q_prod = db.query(
            SaleTransaction.product_name,
            SaleTransaction.category,
            func.count(distinct(SaleTransaction.order_id)).label("return_count"),
            func.sum(SaleTransaction.sales).label("returned_revenue")
        ).filter(SaleTransaction.is_returned == True)
        q_prod = cls._apply_filters(q_prod, filters)
        q_prod = q_prod.group_by(SaleTransaction.product_name, SaleTransaction.category).order_by(desc("return_count")).limit(5)
        prod_rows = q_prod.all()

        top_prods = [{
            "product_name": r.product_name,
            "category": r.category,
            "return_count": int(r.return_count),
            "returned_revenue": round(float(r.returned_revenue or 0.0), 2)
        } for r in prod_rows]

        # Top returned customers
        q_cust = db.query(
            SaleTransaction.customer_name,
            SaleTransaction.country,
            func.count(distinct(SaleTransaction.order_id)).label("return_count"),
            func.sum(SaleTransaction.sales).label("returned_revenue")
        ).filter(SaleTransaction.is_returned == True)
        q_cust = cls._apply_filters(q_cust, filters)
        q_cust = q_cust.group_by(SaleTransaction.customer_name, SaleTransaction.country).order_by(desc("return_count")).limit(5)
        cust_rows = q_cust.all()

        top_custs = [{
            "customer_name": r.customer_name,
            "country": r.country,
            "return_count": int(r.return_count),
            "returned_revenue": round(float(r.returned_revenue or 0.0), 2)
        } for r in cust_rows]

        return ReturnsResponse(
            total_returns=kpis.total_returned_orders,
            return_rate=kpis.return_rate,
            returned_revenue=kpis.returned_revenue,
            top_returned_products=top_prods,
            top_returned_customers=top_custs
        )

    @classmethod
    def get_dynamic_insights(cls, db: Session, filters: FilterParams) -> DynamicInsightsResponse:
        """Dynamically generate natural-language business insights based on real ranking calculations."""
        kpis = cls.get_kpis(db, filters)
        categories = cls.get_category_performance(db, filters)
        top_loss = cls.get_loss_making_products(db, filters, limit=1)
        geography = cls.get_geography_analysis(db, filters, limit=1)
        discount = cls.get_discount_impact(db, filters)

        insights = []

        # 1. Overall Performance Insight
        year_ctx = f"in {filters.year}" if filters.year else "across all historical periods"
        insights.append(DynamicInsightItem(
            title=f"Revenue & Profit Summary ({year_ctx})",
            description=f"Generated ${kpis.total_revenue:,.2f} in gross sales with a net profit of ${kpis.total_profit:,.2f}, delivering an overall commercial profit margin of {kpis.profit_margin:.2f}%.",
            category="sales",
            status="positive" if kpis.profit_margin > 10 else ("neutral" if kpis.profit_margin > 0 else "negative")
        ))

        # 2. Leading Category Insight
        if categories:
            top_cat = categories[0]
            insights.append(DynamicInsightItem(
                title=f"Category Leader: {top_cat.category}",
                description=f"{top_cat.category} is the primary revenue driver, contributing ${top_cat.revenue:,.2f} ({top_cat.share_of_total:.1f}% of total revenue) with a {top_cat.profit_margin:.1f}% profit margin.",
                category="category",
                status="positive"
            ))

        # 3. Loss-Maker Risk Insight
        if top_loss:
            worst = top_loss[0]
            insights.append(DynamicInsightItem(
                title=f"Margin Drainage Alert: {worst.product_name[:35]}...",
                description=f"This product created the largest commercial loss at -${abs(worst.profit):,.2f} on ${worst.revenue:,.2f} sales with an average discount rate of {worst.avg_discount:.1f}%.",
                category="risk",
                status="negative"
            ))

        # 4. Top Geographical Territory
        if geography:
            top_geo = geography[0]
            insights.append(DynamicInsightItem(
                title=f"Top Geographical Market: {top_geo.country}",
                description=f"{top_geo.country} ({top_geo.region} region) produced ${top_geo.revenue:,.2f} across {top_geo.orders:,} orders with a net margin of {top_geo.profit_margin:.1f}%.",
                category="geography",
                status="info"
            ))

        # 5. Discounting Impact Insight
        severe_discount = next((d for d in discount if d.min_discount >= 0.3), None)
        if severe_discount and severe_discount.order_count > 0:
            insights.append(DynamicInsightItem(
                title=f"Discounting Elasticity Warning ({severe_discount.discount_band})",
                description=f"Orders discounted at >30% resulted in a profit margin of {severe_discount.profit_margin:.1f}% with {severe_discount.loss_orders_count:,} unprofitable transactions.",
                category="discount",
                status="negative" if severe_discount.profit_margin < 0 else "neutral"
            ))

        return DynamicInsightsResponse(insights=insights)

    @classmethod
    def get_filter_options(cls, db: Session) -> FilterOptionsResponse:
        """Extract unique dynamic filter options present in the actual database."""
        years = [y[0] for y in db.query(distinct(SaleTransaction.year)).order_by(SaleTransaction.year.desc()).all() if y[0]]
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        months = [
            {"number": 1, "name": "January"}, {"number": 2, "name": "February"},
            {"number": 3, "name": "March"}, {"number": 4, "name": "April"},
            {"number": 5, "name": "May"}, {"number": 6, "name": "June"},
            {"number": 7, "name": "July"}, {"number": 8, "name": "August"},
            {"number": 9, "name": "September"}, {"number": 10, "name": "October"},
            {"number": 11, "name": "November"}, {"number": 12, "name": "December"}
        ]
        countries = [c[0] for c in db.query(distinct(SaleTransaction.country)).order_by(SaleTransaction.country.asc()).all() if c[0]]
        markets = [m[0] for m in db.query(distinct(SaleTransaction.market)).order_by(SaleTransaction.market.asc()).all() if m[0]]
        regions = [r[0] for r in db.query(distinct(SaleTransaction.region)).order_by(SaleTransaction.region.asc()).all() if r[0]]
        categories = [c[0] for c in db.query(distinct(SaleTransaction.category)).order_by(SaleTransaction.category.asc()).all() if c[0]]
        sub_categories = [sc[0] for sc in db.query(distinct(SaleTransaction.sub_category)).order_by(SaleTransaction.sub_category.asc()).all() if sc[0]]
        segments = [s[0] for s in db.query(distinct(SaleTransaction.segment)).order_by(SaleTransaction.segment.asc()).all() if s[0]]
        ship_modes = [sm[0] for sm in db.query(distinct(SaleTransaction.ship_mode)).order_by(SaleTransaction.ship_mode.asc()).all() if sm[0]]
        order_statuses = ["Completed", "Returned"]

        min_date = db.query(func.min(SaleTransaction.order_date)).scalar()
        max_date = db.query(func.max(SaleTransaction.order_date)).scalar()

        return FilterOptionsResponse(
            years=years,
            quarters=quarters,
            months=months,
            countries=countries,
            markets=markets,
            regions=regions,
            categories=categories,
            sub_categories=sub_categories,
            segments=segments,
            ship_modes=ship_modes,
            order_statuses=order_statuses,
            date_range={
                "min_date": str(min_date) if min_date else "",
                "max_date": str(max_date) if max_date else ""
            }
        )
