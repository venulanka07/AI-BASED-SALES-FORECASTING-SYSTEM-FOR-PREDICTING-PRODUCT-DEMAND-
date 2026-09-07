"""
AI-Based Sales Forecasting System for Predicting Product Demand and Revenue Trends
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style for visualizations
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def generate_sales_data(n_days=365, n_products=10):
    """Generate synthetic sales data"""
    np.random.seed(42)
    
    data = []
    base_date = datetime(2023, 1, 1)
    
    for day in range(n_days):
        current_date = base_date + timedelta(days=day)
        day_of_week = current_date.weekday()
        month = current_date.month
        
        for product_id in range(1, n_products + 1):
            # Base demand
            base_demand = 50 + (product_id * 10)
            
            # Seasonal factor
            seasonal = 1 + 0.3 * np.sin(2 * np.pi * month / 12)
            
            # Day of week factor (higher on weekends)
            dow_factor = 1.2 if day_of_week >= 4 else 0.9
            
            # Random promotion
            promotion = 1 + (0.2 if np.random.random() < 0.1 else 0)
            
            # Holiday effect
            is_holiday = 1 if month in [12, 1] else 0
            holiday_factor = 1.3 if is_holiday else 1.0
            
            # Calculate demand and price
            demand = int(base_demand * seasonal * dow_factor * promotion * holiday_factor + np.random.normal(0, 5))
            demand = max(10, demand)
            
            price = 20 + (product_id * 5) + np.random.normal(0, 2)
            price = max(10, price)
            
            revenue = demand * price
            
            data.append({
                'Date': current_date,
                'Product_ID': product_id,
                'Product_Name': f'Product_{product_id}',
                'Demand': demand,
                'Price': round(price, 2),
                'Revenue': round(revenue, 2),
                'Day_of_Week': day_of_week,
                'Month': month,
                'Is_Holiday': is_holiday,
                'Is_Promotion': 1 if promotion > 1 else 0,
                'Seasonal_Index': round(seasonal, 2),
                'Day_Number': day
            })
    
    return pd.DataFrame(data)

def prepare_features(df):
    """Prepare features for modeling"""
    df_copy = df.copy()
    
    # Group by date for daily totals
    daily_data = df_copy.groupby('Date').agg({
        'Demand': 'sum',
        'Revenue': 'sum',
        'Is_Holiday': 'first',
        'Is_Promotion': 'sum',
        'Day_of_Week': 'first',
        'Month': 'first',
        'Day_Number': 'first'
    }).reset_index()
    
    # Add lagged features
    for lag in [1, 7, 30]:
        daily_data[f'Demand_Lag_{lag}'] = daily_data['Demand'].shift(lag)
        daily_data[f'Revenue_Lag_{lag}'] = daily_data['Revenue'].shift(lag)
    
    # Add rolling averages
    for window in [7, 14, 30]:
        daily_data[f'Demand_MA_{window}'] = daily_data['Demand'].rolling(window=window).mean()
        daily_data[f'Revenue_MA_{window}'] = daily_data['Revenue'].rolling(window=window).mean()
    
    # Drop NaN values
    daily_data = daily_data.dropna()
    
    return daily_data

def train_models(df):
    """Train multiple forecasting models"""
    # Prepare features
    feature_cols = [col for col in df.columns if col not in ['Date', 'Demand', 'Revenue']]
    
    X = df[feature_cols]
    y_demand = df['Demand']
    y_revenue = df['Revenue']
    
    # Split data
    X_train, X_test, y_demand_train, y_demand_test = train_test_split(
        X, y_demand, test_size=0.2, random_state=42
    )
    _, _, y_revenue_train, y_revenue_test = train_test_split(
        X, y_revenue, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    models = {}
    results = []
    
    # Train Demand Models
    print("\n[1] Training Demand Forecasting Models...")
    
    # Linear Regression
    lr_demand = LinearRegression()
    lr_demand.fit(X_train_scaled, y_demand_train)
    y_pred = lr_demand.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_demand_test, y_pred))
    mae = mean_absolute_error(y_demand_test, y_pred)
    r2 = r2_score(y_demand_test, y_pred)
    mape = np.mean(np.abs((y_demand_test - y_pred) / y_demand_test)) * 100
    
    models['LR_Demand'] = lr_demand
    results.append({
        'Model': 'Linear Regression (Demand)',
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R2_Score': round(r2, 4),
        'MAPE': round(mape, 2)
    })
    print(f"Linear Regression (Demand) - RMSE: {rmse:.2f}, R²: {r2:.4f}")
    
    # Random Forest
    rf_demand = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_demand.fit(X_train_scaled, y_demand_train)
    y_pred = rf_demand.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_demand_test, y_pred))
    mae = mean_absolute_error(y_demand_test, y_pred)
    r2 = r2_score(y_demand_test, y_pred)
    mape = np.mean(np.abs((y_demand_test - y_pred) / y_demand_test)) * 100
    
    models['RF_Demand'] = rf_demand
    results.append({
        'Model': 'Random Forest (Demand)',
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R2_Score': round(r2, 4),
        'MAPE': round(mape, 2)
    })
    print(f"Random Forest (Demand) - RMSE: {rmse:.2f}, R²: {r2:.4f}")
    
    # Gradient Boosting
    gb_demand = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb_demand.fit(X_train_scaled, y_demand_train)
    y_pred = gb_demand.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_demand_test, y_pred))
    mae = mean_absolute_error(y_demand_test, y_pred)
    r2 = r2_score(y_demand_test, y_pred)
    mape = np.mean(np.abs((y_demand_test - y_pred) / y_demand_test)) * 100
    
    models['GB_Demand'] = gb_demand
    results.append({
        'Model': 'Gradient Boosting (Demand)',
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R2_Score': round(r2, 4),
        'MAPE': round(mape, 2)
    })
    print(f"Gradient Boosting (Demand) - RMSE: {rmse:.2f}, R²: {r2:.4f}")
    
    # Train Revenue Models
    print("\n[2] Training Revenue Forecasting Models...")
    
    # Linear Regression
    lr_revenue = LinearRegression()
    lr_revenue.fit(X_train_scaled, y_revenue_train)
    y_pred = lr_revenue.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_revenue_test, y_pred))
    mae = mean_absolute_error(y_revenue_test, y_pred)
    r2 = r2_score(y_revenue_test, y_pred)
    mape = np.mean(np.abs((y_revenue_test - y_pred) / y_revenue_test)) * 100
    
    models['LR_Revenue'] = lr_revenue
    results.append({
        'Model': 'Linear Regression (Revenue)',
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R2_Score': round(r2, 4),
        'MAPE': round(mape, 2)
    })
    print(f"Linear Regression (Revenue) - RMSE: {rmse:.2f}, R²: {r2:.4f}")
    
    # Random Forest
    rf_revenue = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_revenue.fit(X_train_scaled, y_revenue_train)
    y_pred = rf_revenue.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_revenue_test, y_pred))
    mae = mean_absolute_error(y_revenue_test, y_pred)
    r2 = r2_score(y_revenue_test, y_pred)
    mape = np.mean(np.abs((y_revenue_test - y_pred) / y_revenue_test)) * 100
    
    models['RF_Revenue'] = rf_revenue
    results.append({
        'Model': 'Random Forest (Revenue)',
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R2_Score': round(r2, 4),
        'MAPE': round(mape, 2)
    })
    print(f"Random Forest (Revenue) - RMSE: {rmse:.2f}, R²: {r2:.4f}")
    
    # Gradient Boosting
    gb_revenue = GradientBoostingRegressor(n_estimators=100, random_state=42)
    gb_revenue.fit(X_train_scaled, y_revenue_train)
    y_pred = gb_revenue.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_revenue_test, y_pred))
    mae = mean_absolute_error(y_revenue_test, y_pred)
    r2 = r2_score(y_revenue_test, y_pred)
    mape = np.mean(np.abs((y_revenue_test - y_pred) / y_revenue_test)) * 100
    
    models['GB_Revenue'] = gb_revenue
    results.append({
        'Model': 'Gradient Boosting (Revenue)',
        'RMSE': round(rmse, 2),
        'MAE': round(mae, 2),
        'R2_Score': round(r2, 4),
        'MAPE': round(mape, 2)
    })
    print(f"Gradient Boosting (Revenue) - RMSE: {rmse:.2f}, R²: {r2:.4f}")
    
    return models, X_test_scaled, y_demand_test, y_revenue_test, scaler, X, results

def plot_sales_trends(df):
    """Plot sales trends"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Sales Trends and Patterns Analysis', fontsize=16, fontweight='bold')
    
    # Daily demand trend
    axes[0, 0].plot(df['Date'], df['Demand'], linewidth=2, color='#3498db')
    axes[0, 0].fill_between(df['Date'], df['Demand'], alpha=0.3, color='#3498db')
    axes[0, 0].set_title('Daily Demand Trend', fontweight='bold')
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Demand Units')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Daily revenue trend
    axes[0, 1].plot(df['Date'], df['Revenue'], linewidth=2, color='#2ecc71')
    axes[0, 1].fill_between(df['Date'], df['Revenue'], alpha=0.3, color='#2ecc71')
    axes[0, 1].set_title('Daily Revenue Trend', fontweight='bold')
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('Revenue ($)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Monthly demand distribution
    monthly_demand = df.groupby('Month')['Demand'].sum()
    axes[1, 0].bar(monthly_demand.index, monthly_demand.values, color='#e74c3c', alpha=0.7)
    axes[1, 0].set_title('Monthly Demand Distribution', fontweight='bold')
    axes[1, 0].set_xlabel('Month')
    axes[1, 0].set_ylabel('Total Demand')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Day of week analysis
    dow_demand = df.groupby('Day_of_Week')['Demand'].mean()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    axes[1, 1].bar(range(7), dow_demand.values, color='#f39c12', alpha=0.7)
    axes[1, 1].set_xticks(range(7))
    axes[1, 1].set_xticklabels(days, rotation=45)
    axes[1, 1].set_title('Average Demand by Day of Week', fontweight='bold')
    axes[1, 1].set_ylabel('Average Demand')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/sales_trends.png', dpi=300, bbox_inches='tight')
    print("Saved: sales_trends.png")
    plt.close()

def plot_model_comparison(results_df):
    """Plot model performance comparison"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Model Performance Comparison', fontsize=16, fontweight='bold')
    
    metrics = ['RMSE', 'MAE', 'R2_Score', 'MAPE']
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]
        bars = ax.bar(range(len(results_df)), results_df[metric].values, color=colors, alpha=0.7)
        ax.set_title(f'{metric} Comparison', fontweight='bold')
        ax.set_ylabel(metric)
        ax.set_xticks(range(len(results_df)))
        ax.set_xticklabels([m.split('(')[0].strip() for m in results_df['Model']], rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/sales_model_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: sales_model_comparison.png")
    plt.close()

def plot_predictions_vs_actual(y_actual, y_pred_lr, y_pred_rf, y_pred_gb, metric_name='Demand'):
    """Plot predictions vs actual values"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle(f'{metric_name} Predictions vs Actual Values', fontsize=14, fontweight='bold')
    
    predictions = [y_pred_lr, y_pred_rf, y_pred_gb]
    model_names = ['Linear Regression', 'Random Forest', 'Gradient Boosting']
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    
    for idx, (ax, pred, name, color) in enumerate(zip(axes, predictions, model_names, colors)):
        ax.scatter(y_actual, pred, alpha=0.5, color=color, s=50)
        min_val = min(y_actual.min(), pred.min())
        max_val = max(y_actual.max(), pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', lw=2, label='Perfect Prediction')
        ax.set_xlabel('Actual Values', fontweight='bold')
        ax.set_ylabel('Predicted Values', fontweight='bold')
        ax.set_title(name, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'/home/ubuntu/sales_predictions_vs_actual_{metric_name.lower()}.png', dpi=300, bbox_inches='tight')
    print(f"Saved: sales_predictions_vs_actual_{metric_name.lower()}.png")
    plt.close()

def plot_feature_importance(models, feature_names):
    """Plot feature importance"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Feature Importance Analysis', fontsize=16, fontweight='bold')
    
    model_keys = ['RF_Demand', 'GB_Demand', 'RF_Revenue', 'GB_Revenue']
    titles = ['Random Forest (Demand)', 'Gradient Boosting (Demand)', 'Random Forest (Revenue)', 'Gradient Boosting (Revenue)']
    
    for idx, (ax, key, title) in enumerate(zip(axes.flat, model_keys, titles)):
        model = models[key]
        importances = model.feature_importances_
        indices = np.argsort(importances)[-10:]
        
        ax.barh(range(len(indices)), importances[indices], color='#3498db', alpha=0.7)
        ax.set_yticks(range(len(indices)))
        ax.set_yticklabels([feature_names[i] for i in indices])
        ax.set_xlabel('Importance', fontweight='bold')
        ax.set_title(title, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/sales_feature_importance.png', dpi=300, bbox_inches='tight')
    print("Saved: sales_feature_importance.png")
    plt.close()

def plot_forecast_30days(df, models, scaler, X, feature_names):
    """Plot 30-day forecast"""
    # Use last day's features as base
    last_features = X.iloc[-1:].values
    
    # Generate 30-day forecast
    forecast_demand = []
    forecast_revenue = []
    
    best_demand_model = models['GB_Demand']
    best_revenue_model = models['GB_Revenue']
    
    for day in range(30):
        # Scale features
        scaled_features = scaler.transform(last_features)
        
        # Predict
        demand_pred = best_demand_model.predict(scaled_features)[0]
        revenue_pred = best_revenue_model.predict(scaled_features)[0]
        
        forecast_demand.append(max(0, demand_pred))
        forecast_revenue.append(max(0, revenue_pred))
    
    # Plot
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle('30-Day Sales Forecast', fontsize=16, fontweight='bold')
    
    days = range(1, 31)
    
    # Demand forecast
    axes[0].plot(days, forecast_demand, marker='o', linewidth=2, markersize=6, color='#3498db')
    axes[0].fill_between(days, forecast_demand, alpha=0.3, color='#3498db')
    axes[0].set_title('Demand Forecast (30 Days)', fontweight='bold')
    axes[0].set_xlabel('Day')
    axes[0].set_ylabel('Demand Units')
    axes[0].grid(True, alpha=0.3)
    
    # Revenue forecast
    axes[1].plot(days, forecast_revenue, marker='o', linewidth=2, markersize=6, color='#2ecc71')
    axes[1].fill_between(days, forecast_revenue, alpha=0.3, color='#2ecc71')
    axes[1].set_title('Revenue Forecast (30 Days)', fontweight='bold')
    axes[1].set_xlabel('Day')
    axes[1].set_ylabel('Revenue ($)')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('/home/ubuntu/sales_30day_forecast.png', dpi=300, bbox_inches='tight')
    print("Saved: sales_30day_forecast.png")
    plt.close()
    
    return forecast_demand, forecast_revenue

def main():
    print("="*80)
    print("AI-BASED SALES FORECASTING SYSTEM")
    print("="*80)
    
    print("\n[1] Generating sales data...")
    sales_df = generate_sales_data(n_days=365, n_products=10)
    sales_df.to_csv('/home/ubuntu/sales_data.csv', index=False)
    print(f"Generated {len(sales_df)} sales records")
    
    print("\n[2] Preparing features...")
    daily_df = prepare_features(sales_df)
    print(f"Prepared {len(daily_df)} daily records with features")
    
    print("\n[3] Training forecasting models...")
    models, X_test, y_demand_test, y_revenue_test, scaler, X_train, results = train_models(daily_df)
    results_df = pd.DataFrame(results)
    results_df.to_csv('/home/ubuntu/sales_model_results.csv', index=False)
    print("\nModel Results:")
    print(results_df.to_string(index=False))
    
    print("\n[4] Generating visualizations...")
    plot_sales_trends(daily_df)
    plot_model_comparison(results_df)
    
    # Get predictions for comparison
    y_pred_lr_demand = models['LR_Demand'].predict(X_test)
    y_pred_rf_demand = models['RF_Demand'].predict(X_test)
    y_pred_gb_demand = models['GB_Demand'].predict(X_test)
    plot_predictions_vs_actual(y_demand_test, y_pred_lr_demand, y_pred_rf_demand, y_pred_gb_demand, 'Demand')
    
    y_pred_lr_revenue = models['LR_Revenue'].predict(X_test)
    y_pred_rf_revenue = models['RF_Revenue'].predict(X_test)
    y_pred_gb_revenue = models['GB_Revenue'].predict(X_test)
    plot_predictions_vs_actual(y_revenue_test, y_pred_lr_revenue, y_pred_rf_revenue, y_pred_gb_revenue, 'Revenue')
    
    feature_names = [col for col in daily_df.columns if col not in ['Date', 'Demand', 'Revenue']]
    plot_feature_importance(models, feature_names)
    
    forecast_demand, forecast_revenue = plot_forecast_30days(daily_df, models, scaler, X_train, feature_names)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE - All visualizations saved")
    print("="*80)

if __name__ == "__main__":
    main()
