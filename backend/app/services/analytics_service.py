import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc, asc
from backend.app.models.sales import SaleTransaction
from backend.app.schemas.analytics import FilterParams

class AnalyticsService:
    """Core analytical computation engine executing dynamic SQL and Pandas aggregations."""

    @classmethod
    def apply_filters(cls, query, filters: Optional[FilterParams]):
        if not filters:
            return query
        
        if filters.start_date:
            try:
                s_date = datetime.strptime(filters.start_date, "%Y-%m-%d").date()
                query = query.filter(SaleTransaction.order_date >= s_date)
            except Exception:
                pass
        if filters.end_date:
            try:
                e_date = datetime.strptime(filters.end_date, "%Y-%m-%d").date()
                query = query.filter(SaleTransaction.order_date <= e_date)
            except Exception:
                pass
        if filters.region and filters.region.lower() != "all":
            query = query.filter(SaleTransaction.region == filters.region)
        if filters.state and filters.state.lower() != "all":
            query = query.filter(SaleTransaction.state == filters.state)
        if filters.category and filters.category.lower() != "all":
            query = query.filter(SaleTransaction.category == filters.category)
        if filters.sub_category and filters.sub_category.lower() != "all":
            query = query.filter(SaleTransaction.sub_category == filters.sub_category)
        if filters.segment and filters.segment.lower() != "all":
            query = query.filter(SaleTransaction.segment == filters.segment)
        if filters.ship_mode and filters.ship_mode.lower() != "all":
            query = query.filter(SaleTransaction.ship_mode == filters.ship_mode)
        if filters.min_sales is not None:
            query = query.filter(SaleTransaction.sales >= filters.min_sales)
        if filters.max_sales is not None:
            query = query.filter(SaleTransaction.sales <= filters.max_sales)
            
        return query

    @classmethod
    def get_kpis(cls, db: Session, filters: Optional[FilterParams] = None) -> Dict[str, Any]:
        query = db.query(
            func.sum(SaleTransaction.sales).label("total_sales"),
            func.sum(SaleTransaction.profit).label("total_profit"),
            func.count(distinct(SaleTransaction.order_id)).label("total_orders"),
            func.count(distinct(SaleTransaction.customer_id)).label("total_customers"),
            func.sum(SaleTransaction.quantity).label("total_quantity"),
            func.avg(SaleTransaction.shipping_days).label("avg_shipping_days"),
            func.avg(SaleTransaction.discount).label("avg_discount")
        )
        query = cls.apply_filters(query, filters)
        res = query.first()

        total_sales = float(res.total_sales or 0.0)
        total_profit = float(res.total_profit or 0.0)
        total_orders = int(res.total_orders or 0)
        total_customers = int(res.total_customers or 0)
        total_quantity = int(res.total_quantity or 0)
        avg_shipping_days = round(float(res.avg_shipping_days or 0.0), 2)
        avg_discount = round(float(res.avg_discount or 0.0) * 100.0, 2)
        avg_order_value = round(total_sales / total_orders, 2) if total_orders > 0 else 0.0
        profit_margin = round((total_profit / total_sales) * 100.0, 2) if total_sales > 0 else 0.0

        return {
            "total_sales": round(total_sales, 2),
            "total_profit": round(total_profit, 2),
            "total_orders": total_orders,
            "total_customers": total_customers,
            "avg_order_value": avg_order_value,
            "profit_margin": profit_margin,
            "total_quantity": total_quantity,
            "avg_shipping_days": avg_shipping_days,
            "avg_discount": avg_discount,
            "sales_growth_yoy": None,
            "profit_growth_yoy": None
        }

    @classmethod
    def get_monthly_trends(cls, db: Session, filters: Optional[FilterParams] = None) -> List[Dict[str, Any]]:
        query = db.query(
            SaleTransaction.year_month,
            SaleTransaction.year,
            SaleTransaction.month,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders")
        ).group_by(SaleTransaction.year_month, SaleTransaction.year, SaleTransaction.month)\
         .order_by(asc(SaleTransaction.year_month))

        query = cls.apply_filters(query, filters)
        rows = query.all()

        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        result = []
        prev_sales = None
        for r in rows:
            sales = float(r.sales or 0.0)
            profit = float(r.profit or 0.0)
            margin = round((profit / sales) * 100.0, 2) if sales > 0 else 0.0
            
            mom_growth = None
            if prev_sales is not None and prev_sales > 0:
                mom_growth = round(((sales - prev_sales) / prev_sales) * 100.0, 2)
            prev_sales = sales

            m_idx = int(r.month) - 1
            m_name = month_names[m_idx] if 0 <= m_idx < 12 else str(r.month)

            result.append({
                "year_month": r.year_month,
                "year": int(r.year),
                "month": int(r.month),
                "month_name": m_name,
                "sales": round(sales, 2),
                "profit": round(profit, 2),
                "orders": int(r.orders),
                "profit_margin": margin,
                "sales_mom_growth": mom_growth,
                "sales_yoy_growth": None
            })
        return result

    @classmethod
    def get_category_performance(cls, db: Session, filters: Optional[FilterParams] = None) -> List[Dict[str, Any]]:
        query = db.query(
            SaleTransaction.category,
            SaleTransaction.sub_category,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.sum(SaleTransaction.quantity).label("quantity"),
            func.count(distinct(SaleTransaction.order_id)).label("orders")
        ).group_by(SaleTransaction.category, SaleTransaction.sub_category)\
         .order_by(SaleTransaction.category, desc("sales"))

        query = cls.apply_filters(query, filters)
        rows = query.all()

        categories_dict = {}
        for r in rows:
            cat = r.category
            if cat not in categories_dict:
                categories_dict[cat] = {
                    "category": cat,
                    "sales": 0.0,
                    "profit": 0.0,
                    "quantity": 0,
                    "orders": 0,
                    "sub_categories": []
                }
            
            s = float(r.sales or 0.0)
            p = float(r.profit or 0.0)
            q = int(r.quantity or 0)
            o = int(r.orders or 0)
            m = round((p / s) * 100.0, 2) if s > 0 else 0.0

            categories_dict[cat]["sales"] += s
            categories_dict[cat]["profit"] += p
            categories_dict[cat]["quantity"] += q
            categories_dict[cat]["orders"] += o
            categories_dict[cat]["sub_categories"].append({
                "sub_category": r.sub_category,
                "sales": round(s, 2),
                "profit": round(p, 2),
                "quantity": q,
                "orders": o,
                "profit_margin": m
            })

        output = []
        for cat, data in categories_dict.items():
            tot_s = data["sales"]
            tot_p = data["profit"]
            margin = round((tot_p / tot_s) * 100.0, 2) if tot_s > 0 else 0.0
            output.append({
                "category": cat,
                "sales": round(tot_s, 2),
                "profit": round(tot_p, 2),
                "quantity": data["quantity"],
                "orders": data["orders"],
                "profit_margin": margin,
                "sub_categories": sorted(data["sub_categories"], key=lambda x: x["sales"], reverse=True)
            })

        return sorted(output, key=lambda x: x["sales"], reverse=True)

    @classmethod
    def get_product_performance(cls, db: Session, filters: Optional[FilterParams] = None, sort_by: str = "sales", ascending: bool = False, limit: int = 10) -> List[Dict[str, Any]]:
        query = db.query(
            SaleTransaction.product_id,
            SaleTransaction.product_name,
            SaleTransaction.category,
            SaleTransaction.sub_category,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.sum(SaleTransaction.quantity).label("quantity")
        ).group_by(
            SaleTransaction.product_id,
            SaleTransaction.product_name,
            SaleTransaction.category,
            SaleTransaction.sub_category
        )

        query = cls.apply_filters(query, filters)

        order_col = desc("sales")
        if sort_by == "profit":
            order_col = asc("profit") if ascending else desc("profit")
        elif sort_by == "quantity":
            order_col = asc("quantity") if ascending else desc("quantity")
        elif sort_by == "sales":
            order_col = asc("sales") if ascending else desc("sales")

        query = query.order_by(order_col).limit(limit)
        rows = query.all()

        result = []
        for r in rows:
            s = float(r.sales or 0.0)
            p = float(r.profit or 0.0)
            q = int(r.quantity or 0)
            m = round((p / s) * 100.0, 2) if s > 0 else 0.0
            result.append({
                "product_id": r.product_id,
                "product_name": r.product_name,
                "category": r.category,
                "sub_category": r.sub_category,
                "sales": round(s, 2),
                "profit": round(p, 2),
                "quantity": q,
                "profit_margin": m
            })
        return result

    @classmethod
    def get_regional_analysis(cls, db: Session, filters: Optional[FilterParams] = None) -> List[Dict[str, Any]]:
        query = db.query(
            SaleTransaction.region,
            SaleTransaction.state,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders"),
            func.count(distinct(SaleTransaction.customer_id)).label("customers")
        ).group_by(SaleTransaction.region, SaleTransaction.state)\
         .order_by(SaleTransaction.region, desc("sales"))

        query = cls.apply_filters(query, filters)
        rows = query.all()

        regional_dict = {}
        for r in rows:
            reg = r.region
            if reg not in regional_dict:
                regional_dict[reg] = {
                    "region": reg,
                    "sales": 0.0,
                    "profit": 0.0,
                    "orders": 0,
                    "customers": 0,
                    "top_states": []
                }
            s = float(r.sales or 0.0)
            p = float(r.profit or 0.0)
            o = int(r.orders or 0)
            c = int(r.customers or 0)
            m = round((p / s) * 100.0, 2) if s > 0 else 0.0

            regional_dict[reg]["sales"] += s
            regional_dict[reg]["profit"] += p
            regional_dict[reg]["orders"] += o
            regional_dict[reg]["customers"] += c
            regional_dict[reg]["top_states"].append({
                "state": r.state,
                "sales": round(s, 2),
                "profit": round(p, 2),
                "orders": o,
                "profit_margin": m
            })

        output = []
        for reg, data in regional_dict.items():
            tot_s = data["sales"]
            tot_p = data["profit"]
            margin = round((tot_p / tot_s) * 100.0, 2) if tot_s > 0 else 0.0
            output.append({
                "region": reg,
                "sales": round(tot_s, 2),
                "profit": round(tot_p, 2),
                "orders": data["orders"],
                "customers": data["customers"],
                "profit_margin": margin,
                "top_states": sorted(data["top_states"], key=lambda x: x["sales"], reverse=True)
            })

        return sorted(output, key=lambda x: x["sales"], reverse=True)

    @classmethod
    def get_state_performance(cls, db: Session, filters: Optional[FilterParams] = None) -> List[Dict[str, Any]]:
        query = db.query(
            SaleTransaction.state,
            SaleTransaction.region,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders")
        ).group_by(SaleTransaction.state, SaleTransaction.region)\
         .order_by(desc("sales"))

        query = cls.apply_filters(query, filters)
        rows = query.all()

        result = []
        for r in rows:
            s = float(r.sales or 0.0)
            p = float(r.profit or 0.0)
            m = round((p / s) * 100.0, 2) if s > 0 else 0.0
            result.append({
                "state": r.state,
                "region": r.region,
                "sales": round(s, 2),
                "profit": round(p, 2),
                "orders": int(r.orders),
                "profit_margin": m
            })
        return result

    @classmethod
    def get_customer_analysis(cls, db: Session, filters: Optional[FilterParams] = None) -> Dict[str, Any]:
        # 1. Segment Breakdown
        seg_query = db.query(
            SaleTransaction.segment,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.customer_id)).label("customers"),
            func.count(distinct(SaleTransaction.order_id)).label("orders")
        ).group_by(SaleTransaction.segment).order_by(desc("sales"))
        seg_query = cls.apply_filters(seg_query, filters)
        seg_rows = seg_query.all()

        segments = []
        for r in seg_rows:
            s = float(r.sales or 0.0)
            p = float(r.profit or 0.0)
            c = int(r.customers or 0)
            o = int(r.orders or 0)
            m = round((p / s) * 100.0, 2) if s > 0 else 0.0
            avg_spend = round(s / c, 2) if c > 0 else 0.0
            segments.append({
                "segment": r.segment,
                "sales": round(s, 2),
                "profit": round(p, 2),
                "customers": c,
                "orders": o,
                "avg_spend": avg_spend,
                "profit_margin": m
            })

        # 2. Top Customers
        cust_query = db.query(
            SaleTransaction.customer_id,
            SaleTransaction.customer_name,
            SaleTransaction.segment,
            func.sum(SaleTransaction.sales).label("sales"),
            func.sum(SaleTransaction.profit).label("profit"),
            func.count(distinct(SaleTransaction.order_id)).label("orders")
        ).group_by(
            SaleTransaction.customer_id,
            SaleTransaction.customer_name,
            SaleTransaction.segment
        ).order_by(desc("sales")).limit(10)
        cust_query = cls.apply_filters(cust_query, filters)
        cust_rows = cust_query.all()

        top_customers = []
        for r in cust_rows:
            s = float(r.sales or 0.0)
            p = float(r.profit or 0.0)
            o = int(r.orders or 0)
            aov = round(s / o, 2) if o > 0 else 0.0
            top_customers.append({
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "segment": r.segment,
                "total_spend": round(s, 2),
                "total_profit": round(p, 2),
                "order_count": o,
                "avg_order_value": aov
            })

        return {
            "segments": segments,
            "top_customers": top_customers
        }

    @classmethod
    def get_rfm_segmentation(cls, db: Session, filters: Optional[FilterParams] = None) -> List[Dict[str, Any]]:
        """Compute RFM scores and customer segmentation cohorts."""
        query = db.query(
            SaleTransaction.customer_id,
            func.max(SaleTransaction.order_date).label("last_order_date"),
            func.count(distinct(SaleTransaction.order_id)).label("frequency"),
            func.sum(SaleTransaction.sales).label("monetary"),
            func.sum(SaleTransaction.profit).label("profit")
        ).group_by(SaleTransaction.customer_id)
        query = cls.apply_filters(query, filters)
        rows = query.all()

        if not rows:
            return []

        max_date_query = db.query(func.max(SaleTransaction.order_date)).scalar() or datetime.now().date()

        data = []
        for r in rows:
            recency = (max_date_query - r.last_order_date).days if r.last_order_date else 999
            data.append({
                "customer_id": r.customer_id,
                "recency": max(0, recency),
                "frequency": int(r.frequency or 1),
                "monetary": float(r.monetary or 0.0),
                "profit": float(r.profit or 0.0)
            })

        df_rfm = pd.DataFrame(data)
        if len(df_rfm) < 4:
            return [{
                "segment": "All Customers",
                "customer_count": len(df_rfm),
                "avg_recency": round(float(df_rfm["recency"].mean()), 1),
                "avg_frequency": round(float(df_rfm["frequency"].mean()), 1),
                "avg_monetary": round(float(df_rfm["monetary"].mean()), 2),
                "total_revenue": round(float(df_rfm["monetary"].sum()), 2),
                "total_profit": round(float(df_rfm["profit"].sum()), 2)
            }]

        df_rfm["r_score"] = pd.qcut(df_rfm["recency"], 4, labels=[4, 3, 2, 1], duplicates="drop")
        df_rfm["f_score"] = pd.qcut(df_rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4], duplicates="drop")
        df_rfm["m_score"] = pd.qcut(df_rfm["monetary"], 4, labels=[1, 2, 3, 4], duplicates="drop")

        def assign_cohort(row):
            try:
                r = int(row["r_score"])
                fm = (int(row["f_score"]) + int(row["m_score"])) / 2.0
                if r >= 3 and fm >= 3:
                    return "Champions & Loyalists"
                elif r >= 3 and fm < 3:
                    return "Recent / Potential Loyalists"
                elif r < 3 and fm >= 3:
                    return "At Risk / High Spenders"
                else:
                    return "Hibernating / Lost"
            except Exception:
                return "General Customers"

        df_rfm["segment"] = df_rfm.apply(assign_cohort, axis=1)

        cohort_summary = df_rfm.groupby("segment").agg(
            customer_count=("customer_id", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("monetary", "sum"),
            total_profit=("profit", "sum")
        ).reset_index()

        result = []
        for _, row in cohort_summary.iterrows():
            result.append({
                "segment": str(row["segment"]),
                "customer_count": int(row["customer_count"]),
                "avg_recency": round(float(row["avg_recency"]), 1),
                "avg_frequency": round(float(row["avg_frequency"]), 1),
                "avg_monetary": round(float(row["avg_monetary"]), 2),
                "total_revenue": round(float(row["total_revenue"]), 2),
                "total_profit": round(float(row["total_profit"]), 2)
            })

        return sorted(result, key=lambda x: x["total_revenue"], reverse=True)

    @classmethod
    def get_filter_options(cls, db: Session) -> Dict[str, Any]:
        """Fetch distinct values for frontend filter controls."""
        min_date = db.query(func.min(SaleTransaction.order_date)).scalar()
        max_date = db.query(func.max(SaleTransaction.order_date)).scalar()

        regions = [r[0] for r in db.query(distinct(SaleTransaction.region)).order_by(SaleTransaction.region).all() if r[0]]
        states = [s[0] for s in db.query(distinct(SaleTransaction.state)).order_by(SaleTransaction.state).all() if s[0]]
        categories = [c[0] for c in db.query(distinct(SaleTransaction.category)).order_by(SaleTransaction.category).all() if c[0]]
        sub_categories = [sc[0] for sc in db.query(distinct(SaleTransaction.sub_category)).order_by(SaleTransaction.sub_category).all() if sc[0]]
        segments = [sg[0] for sg in db.query(distinct(SaleTransaction.segment)).order_by(SaleTransaction.segment).all() if sg[0]]
        ship_modes = [sm[0] for sm in db.query(distinct(SaleTransaction.ship_mode)).order_by(SaleTransaction.ship_mode).all() if sm[0]]

        return {
            "date_range": {
                "min_date": str(min_date) if min_date else "2014-01-01",
                "max_date": str(max_date) if max_date else "2017-12-31"
            },
            "regions": regions,
            "states": states,
            "categories": categories,
            "sub_categories": sub_categories,
            "segments": segments,
            "ship_modes": ship_modes
        }
