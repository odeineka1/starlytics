import datetime
import statistics
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.rule import Rule
from rich.padding import Padding
from rich.columns import Columns
from collections import Counter
from categories_kw import categories_kw
from google import genai
from google.genai import types
from rich.markdown import Markdown

categories_kw = categories_kw
console = Console()

class StarlyticsEngine:
    def __init__(self):
        self.review_count_general_threshold = 3
        self.review_count_category_threshold = 2
        self.sentiment_threshold = 15
        self.time_delta_hours = 72
        self.recency_weighting = False
        self.ai_model = "gemini-2.5-flash"

    @property
    def review_count_general_threshold(self):
        return self._review_count_general_threshold
    
    @review_count_general_threshold.setter
    def review_count_general_threshold(self, review_count_general_threshold):
        if isinstance(review_count_general_threshold, int) and review_count_general_threshold > -1:
            self._review_count_general_threshold = review_count_general_threshold
        else:
            raise ValueError("❌ Invalid Input: Enter a whole number (e.g., 0, 1, 2)")
    
    @property
    def review_count_category_threshold(self):
        return self._review_count_category_threshold
    
    @review_count_category_threshold.setter
    def review_count_category_threshold(self, review_count_category_threshold):
        if isinstance(review_count_category_threshold, int) and review_count_category_threshold > -1:
            self._review_count_category_threshold = review_count_category_threshold
        else:
            raise ValueError("❌ Invalid Input: Enter a whole number (e.g., 0, 1, 2)")

    @property
    def sentiment_threshold(self):
        return self._sentiment_threshold
    
    @sentiment_threshold.setter
    def sentiment_threshold(self, sentiment_threshold):
        if isinstance(sentiment_threshold, int) and 0 < sentiment_threshold <= 100:
            self._sentiment_threshold = sentiment_threshold
        else:
            raise ValueError("❌ Invalid Input: Enter an integer that is between 1 and 100")
        
    @property
    def time_delta_hours(self):
        return self._time_delta_hours
    
    @time_delta_hours.setter
    def time_delta_hours(self, time_delta_hours):
        if isinstance(time_delta_hours, int) and time_delta_hours > -1:
            self._time_delta_hours = time_delta_hours
        else:
            raise ValueError("❌ Invalid Input: Enter a whole number (e.g., 0, 1, 2)")


    def caculate_category_means(self, all_reviews, engine):
        self.all_reviews = all_reviews

        oe_category = []
        vp_category = []
        pe_category = []
        po_category = []
        other_category = []
        if engine.recency_weighting:
            oe_weights= 0
            vp_weights= 0
            pe_weights= 0
            po_weights= 0
            other_weights= 0
            self.last_review_date = self.all_reviews[0].timestamp
            for review in self.all_reviews:
                recency = (self.last_review_date-review.timestamp).days
                weight = 0.5**(recency/90)
                if "Operational Efficiency" in review.category:
                    oe_category.append(review.sentiment["Operational Efficiency"]*weight)
                    oe_weights += weight
                if "Value Proposition" in review.category:
                    vp_category.append(review.sentiment["Value Proposition"]*weight)
                    vp_weights += weight
                if "Physical Environment" in review.category:
                    pe_category.append(review.sentiment["Physical Environment"]*weight)
                    pe_weights += weight
                if "Product/Offering" in review.category:
                    po_category.append(review.sentiment["Product/Offering"]*weight)
                    po_weights += weight
                if "Other" in review.category:
                    other_category.append(review.sentiment["Other"]*weight)
                    other_weights += weight
            
            if len(oe_category) != 0:
                self.oe_mean = round(sum(oe_category)/oe_weights)
            else:
                self.oe_mean = "No Data"
            if len(vp_category) != 0:
                self.vp_mean = round(sum(vp_category)/vp_weights)
            else:
                self.vp_mean = "No Data"
            if len(pe_category) != 0:
                self.pe_mean = round(sum(pe_category)/pe_weights)
            else:
                self.pe_mean = "No Data"
            if len(po_category) != 0:
                self.po_mean = round(sum(po_category)/po_weights)
            else:
                self.po_mean = "No Data"
            if len(other_category) != 0:
                self.other_mean = round(sum(other_category)/other_weights)
            else:
                self.other_mean = "No Data"

        else:
            for review in self.all_reviews:
                if "Operational Efficiency" in review.category:
                    oe_category.append(review.sentiment["Operational Efficiency"])
                if "Value Proposition" in review.category:
                    vp_category.append(review.sentiment["Value Proposition"])
                if "Physical Environment" in review.category:
                    pe_category.append(review.sentiment["Physical Environment"])
                if "Product/Offering" in review.category:
                    po_category.append(review.sentiment["Product/Offering"])
                if "Other" in review.category:
                    other_category.append(review.sentiment["Other"])

            if len(oe_category) != 0:
                self.oe_mean = round(statistics.mean(oe_category))
            else:
                self.oe_mean = "No Data"
            if len(vp_category) != 0:
                self.vp_mean = round(statistics.mean(vp_category))
            else:
                self.vp_mean = "No Data"
            if len(pe_category) != 0:
                self.pe_mean = round(statistics.mean(pe_category))
            else:
                self.pe_mean = "No Data"
            if len(po_category) != 0:
                self.po_mean = round(statistics.mean(po_category))
            else:
                self.po_mean = "No Data"
            if len(other_category) != 0:
                self.other_mean = round(statistics.mean(other_category))
            else:
                self.other_mean = "No Data"
    
    def generate_trend_text(self):
        self.oe_trend_text = ""
        self.vp_trend_text = ""
        self.pe_trend_text = ""
        self.po_trend_text = ""
        self.other_trend_text = ""
        if self.week_trend_flag:
            try: 
                if self.oe_trend > 5:
                    self.oe_trend_text = Text(f"(latest* week is +{self.oe_trend:.2f} vs. prev. week) Improving!", style="bold green")
                elif self.oe_trend < -5:
                    self.oe_trend_text = Text(f"(latest* week is {self.oe_trend:.2f} vs. prev. week) Declining!", style="bold red")
                else:
                    symbol = "+" if self.oe_trend >= 0 else ""
                    self.oe_trend_text = Text(f"(latest* week is {symbol}{self.oe_trend:.2f} vs. prev. week) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.vp_trend > 5:
                    self.vp_trend_text = Text(f"(latest* week is +{self.vp_trend:.2f} vs. prev. week) Improving!", style="bold green")
                elif self.vp_trend < -5:
                    self.vp_trend_text = Text(f"(latest* week is {self.vp_trend:.2f} vs. prev. week) Declining!", style="bold red")
                else:
                    symbol = "+" if self.vp_trend >= 0 else ""
                    self.vp_trend_text = Text(f"(latest* week is {symbol}{self.vp_trend:.2f} vs. prev. week) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.pe_trend > 5:
                    self.pe_trend_text = Text(f"(latest* week is +{self.pe_trend:.2f} vs. prev. week) Improving!", style="bold green")
                elif self.pe_trend < -5:
                    self.pe_trend_text = Text(f"(latest* week is {self.pe_trend:.2f} vs. prev. week) Declining!", style="bold red")
                else:
                    symbol = "+" if self.pe_trend >= 0 else ""
                    self.pe_trend_text = Text(f"(latest* week is {symbol}{self.pe_trend:.2f} vs. prev. week) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.po_trend > 5:
                    self.po_trend_text = Text(f"(latest* week is +{self.po_trend:.2f} vs. prev. week) Improving!", style="bold green")
                elif self.po_trend < -5:
                    self.po_trend_text = Text(f"(latest* week is {self.po_trend:.2f} vs. prev. week) Declining!", style="bold red")
                else:
                    symbol = "+" if self.po_trend >= 0 else ""
                    self.po_trend_text = Text(f"(latest* week is {symbol}{self.po_trend:.2f} vs. prev. week) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.other_trend > 5:
                    self.other_trend_text = Text(f"(latest* week is +{self.other_trend:.2f} vs. prev. week) Improving!", style="bold green")
                elif self.other_trend < -5:
                    self.other_trend_text = Text(f"(latest* week is {self.other_trend:.2f} vs. prev. week) Declining!", style="bold red")
                else:
                    symbol = "+" if self.other_trend >= 0 else ""
                    self.other_trend_text = Text(f"(latest* week is {symbol}{self.other_trend:.2f} vs. prev. week) Stable.", style="bold yellow")
            except TypeError:
                pass

        elif self.month_trend_flag:
            try: 
                if self.oe_trend > 5:
                    self.oe_trend_text = Text(f"(latest* month is +{self.oe_trend:.2f} vs. prev. month) Improving!", style="bold green")
                elif self.oe_trend < -5:
                    self.oe_trend_text = Text(f"(latest* month is {self.oe_trend:.2f} vs. prev. month) Declining!", style="bold red")
                else:
                    symbol = "+" if self.oe_trend >= 0 else ""
                    self.oe_trend_text = Text(f"(latest* month is {symbol}{self.oe_trend:.2f} vs. prev. month) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.vp_trend > 5:
                    self.vp_trend_text = Text(f"(latest* month is +{self.vp_trend:.2f} vs. prev. month) Improving!", style="bold green")
                elif self.vp_trend < -5:
                    self.vp_trend_text = Text(f"(latest* month is {self.vp_trend:.2f} vs. prev. month) Declining!", style="bold red")
                else:
                    symbol = "+" if self.vp_trend >= 0 else ""
                    self.vp_trend_text = Text(f"(latest* month is {symbol}{self.vp_trend:.2f} vs. prev. month) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.pe_trend > 5:
                    self.pe_trend_text = Text(f"(latest* month is +{self.pe_trend:.2f} vs. prev. month) Improving!", style="bold green")
                elif self.pe_trend < -5:
                    self.pe_trend_text = Text(f"(latest* month is {self.pe_trend:.2f} vs. prev. month) Declining!", style="bold red")
                else:
                    symbol = "+" if self.pe_trend >= 0 else ""
                    self.pe_trend_text = Text(f"(latest* month is {symbol}{self.pe_trend:.2f} vs. prev. month) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.po_trend > 5:
                    self.po_trend_text = Text(f"(latest* month is +{self.po_trend:.2f} vs. prev. month) Improving!", style="bold green")
                elif self.po_trend < -5:
                    self.po_trend_text = Text(f"(latest* month is {self.po_trend:.2f} vs. prev. month) Declining!", style="bold red")
                else:
                    symbol = "+" if self.po_trend >= 0 else ""
                    self.po_trend_text = Text(f"(latest* month is {symbol}{self.po_trend:.2f} vs. prev. month) Stable.", style="bold yellow")
            except TypeError:
                pass

            try:
                if self.other_trend > 5:
                    self.other_trend_text = Text(f"(latest* month is +{self.other_trend:.2f} vs. prev. month) Improving!", style="bold green")
                elif self.other_trend < -5:
                    self.other_trend_text = Text(f"(latest* month is {self.other_trend:.2f} vs. prev. month) Declining!", style="bold red")
                else:
                    symbol = "+" if self.other_trend >= 0 else ""
                    self.other_trend_text = Text(f"(latest* month is {symbol}{self.other_trend:.2f} vs. prev. month) Stable.", style="bold yellow")
            except TypeError:
                pass

    def generate_report(self, reviews_count, total_time, business_name):
        self.generate_trend_text()

        console.print()
        console.print(Rule(style="bright_cyan"))
        console.print(Text(f"★  STARLYTICS REPORT FOR {business_name} ★", style="bold bright_cyan"), justify="center")
        console.print(Text(f"Loaded and analyzed {reviews_count} reviews in {total_time:.2f} seconds"), justify="center")
        console.print(Text(f"Analytics Period: {self.first_review_date} to {self.last_review_date}", style="dim"), justify="center")
        console.print(Rule(style="bright_cyan"))
        console.print()

        table = Table(box=box.ROUNDED, border_style="bright_cyan", header_style="bold bright_cyan", show_lines=True, expand=True)
        table.add_column("Category", style="bold white", min_width=22)
        table.add_column("Score", style="bold", justify="center", min_width=8)
        table.add_column("Trend", min_width=48)

        # Calculate overall trend
        average_trend = 0
        trend_score = 0
        try:
            for trend in [self.oe_trend, self.vp_trend, self.pe_trend, self.po_trend, self.other_trend]:
                try:
                    average_trend += trend
                    trend_score += 1
                except TypeError:
                    pass
            if trend_score != 0:
                average_trend = average_trend/trend_score
            else: 
                average_trend = "No Data"
        except AttributeError:
            average_trend = "No Data"

        average_score = 0
        score_count = 0
        for name, mean, trend_text in [
            ("Operational Efficiency", self.oe_mean, self.oe_trend_text),
            ("Value Proposition", self.vp_mean, self.vp_trend_text),
            ("Physical Environment", self.pe_mean, self.pe_trend_text),
            ("Product/Offering", self.po_mean, self.po_trend_text),
            ("Other", self.other_mean, self.other_trend_text),
        ]:
            try:
                average_score += mean
                score_count += 1
            except TypeError:
                pass
            try:
                score_val = float(mean)
                if score_val >= 65:
                    mean_text = Text(f"{str(mean)}/100", style="bold green")
                elif score_val >= 50:
                    mean_text = Text(f"{str(mean)}/100", style="bold yellow")
                else:
                    mean_text = Text(f"{str(mean)}/100", style="bold red")
            except (TypeError, ValueError):
                mean_text = Text(str(mean), style="dim")
            table.add_row(name, mean_text, trend_text)

        console.print(Padding(table, (0, 2)))
        
        if score_count != 0:
            average_score = average_score/score_count
        else:
            average_score = "No Data"

        if self.week_trend_flag:
            console.print()
            console.print(Padding("[dim]* Trend reflects the change in sentiment between the most recent week in the selected period and the week immediately preceding it[/dim]", (0, 4)))
        elif self.month_trend_flag:
            console.print()
            console.print(Padding("[dim]* Trend reflects the change in sentiment between the most recent month in the selected period and the month immediately preceding it[/dim]", (0, 4)))

        console.print()
        hour_unit = "hour" if self.time_delta_hours == 1 else "hours"
        if self.category_alert_status:
            alert_lines = Text()
            alert_lines.append("🚨  CATEGORY ALERT DETECTED\n\n", style="bold red")
            for category in self.category_flags.keys():
                if self.category_flags[category] > 0:
                    customer_unit = "customer" if self.category_flags[category] == 1 else "customers"
                    alert_lines.append(f"  {self.category_flags[category]} {customer_unit} reported ", style="red")
                    alert_lines.append(f"{category}", style="bold red")
                    alert_lines.append(f" issues within last {self.time_delta_hours} {hour_unit}\n", style="red")
            console.print(Panel(alert_lines, border_style="bold red", box=box.HEAVY, expand=False), justify="center")

        elif self.general_alert_status:
            complaint_unit = "complaint" if self.review_count == 1 else "complaints"
            alert_lines = Text()
            alert_lines.append("🚨  GENERAL ALERT DETECTED\n\n", style="bold yellow")
            alert_lines.append(f"  General sentiment is dropping rapidly. {self.review_count} unrelated {complaint_unit} detected during last {self.time_delta_hours} {hour_unit}.", style="yellow")
            console.print(Panel(alert_lines, border_style="bold yellow", box=box.HEAVY, expand=False), justify="center")
        else:
            console.print(Panel(Text(f"✅  No alerts detected within last {self.time_delta_hours} hours", style="bold green"), border_style="green", box=box.ROUNDED, expand=False), justify="center")

        console.print()
        console.print(Rule(style="bright_cyan"))
        console.print()

        result_table = Table(box=box.HEAVY, border_style="bright_cyan", show_header=False, expand=False)
        result_table.add_column(justify="center")

        if average_score == "No Data":
            score_style = "dim"
        elif average_score >= 65:
            score_style = "bold green"
        elif average_score >= 50:
            score_style = "bold yellow"
        else:
            score_style = "bold red"

        if average_trend == "No Data":
            trend_style = "dim"
            trend_arrow = ""
            trend_label = ""
        elif average_trend >= 0.1:
            trend_style = "bold green"
            trend_arrow = "↑"
            trend_label = "Improving"
        elif average_trend <= -0.1:
            trend_style = "bold red"
            trend_arrow = "↓"
            trend_label = "Declining"
        else:
            trend_style = "bold yellow"
            trend_arrow = "→"
            trend_label = "Stable"

        score_text = Text(justify="center")
        
        # score_text.append("Overall Score: ", style="white")
        score_text.append(f"Overall Score: {int(average_score)}/100\n", style=f"bold {score_style} reverse" if average_score < 50 else f"bold {score_style}") 
        
        score_text.append("───────────────────────────────────\n", style="bold bright_cyan")
        
        if average_trend == "No Data":
            score_text.append(f"Overall Trend: {average_trend}", style=trend_style)
        else:
            score_text.append(f"Overall Trend: {trend_arrow} {average_trend:+.1f} ({trend_label})", style=trend_style)

        console.print(Panel(
            score_text,
            title="[bold bright_cyan] REVIEWS ANALYTIC SUMMARY [/bold bright_cyan]",
            subtitle=f"[bold white]{business_name}[/bold white]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            width=46,
            padding=(1, 2),
        ), justify="center")
        console.print()   

    def generate_battle_report(self, engine1, engine2, reviews_count1, reviews_count2, total_time1, total_time2, business1_name, business2_name):
        engine1.generate_trend_text()
        engine2.generate_trend_text()
        
        console.print()
        console.print(Rule(style="bright_cyan"))
        console.print(Text(f"★  STARLYTICS BATTLE REPORT FOR {business1_name} AND {business2_name} ★", style="bold bright_cyan"), justify="center")
        console.print()
        console.print(Text(f"Loaded and analyzed {reviews_count1} {business1_name} reviews in {total_time1:.2f} seconds"), justify="center")
        console.print(Text(f"Analytics Period: {engine1.first_review_date} to {engine1.last_review_date}", style="dim"), justify="center")
        console.print()
        console.print(Text(f"Loaded and analyzed {reviews_count2} {business2_name} reviews in {total_time2:.2f} seconds"), justify="center")
        console.print(Text(f"Analytics Period: {engine2.first_review_date} to {engine2.last_review_date}", style="dim"), justify="center")
        console.print(Rule(style="bright_cyan"))
        console.print()

        outer = Table(box=box.ROUNDED, border_style="bright_cyan", header_style="bold bright_cyan", show_lines=True, expand=True)
        outer.add_column("Category", style="bold white", min_width=22)
        outer.add_column(f"{business1_name} Score", justify="center", header_style="bold bright_cyan", min_width=12)
        outer.add_column(f"{business1_name} Trend", justify="center", header_style="bold bright_cyan", min_width=36)
        outer.add_column(f"{business2_name} Score", justify="center", header_style="bold bright_cyan", min_width=12)
        outer.add_column(f"{business2_name} Trend", justify="center", header_style="bold bright_cyan", min_width=36)

        # Calculate overall trend
        average_trend1 = 0
        average_trend2 = 0
        trend_score1 = 0
        trend_score2 = 0
        try:
            for trend in [engine1.oe_trend, engine1.vp_trend, engine1.pe_trend, engine1.po_trend, engine1.other_trend]:
                try:
                    average_trend1 += trend
                    trend_score1 += 1
                except TypeError:
                    pass
            if trend_score1 != 0:
                average_trend1 = average_trend1/trend_score1
            else: 
                average_trend1 = "No Data"
        except AttributeError:
            average_trend1 = "No Data"
        
        try:
            for trend in [engine2.oe_trend, engine2.vp_trend, engine2.pe_trend, engine2.po_trend, engine2.other_trend]:
                try:
                    average_trend2 += trend
                    trend_score2 += 1
                except TypeError:
                    pass
            if trend_score2 != 0:
                average_trend2 = average_trend2/trend_score2
            else: 
                average_trend2 = "No Data"
        except AttributeError:
            average_trend2 = "No Data"

        average_score1 = 0
        average_score2 = 0
        score_count1 = 0
        score_count2 = 0
        for name, mean1, trend_text1, mean2, trend_text2 in [
            ("Operational Efficiency", engine1.oe_mean, engine1.oe_trend_text, engine2.oe_mean, engine2.oe_trend_text),
            ("Value Proposition", engine1.vp_mean, engine1.vp_trend_text, engine2.vp_mean, engine2.vp_trend_text),
            ("Physical Environment", engine1.pe_mean, engine1.pe_trend_text, engine2.pe_mean, engine2.pe_trend_text),
            ("Product/Offering", engine1.po_mean, engine1.po_trend_text, engine2.po_mean, engine2.po_trend_text),
            ("Other", engine1.other_mean, engine1.other_trend_text, engine2.other_mean, engine2.other_trend_text),
        ]:
            try:
                average_score1 += mean1
                score_count1 += 1
            except TypeError:
                pass

            try:
                average_score2 += mean2
                score_count2 += 1
            except TypeError:
                pass

            try:
                score_val1 = float(mean1)
                if score_val1 >= 65:
                    mean_text1 = Text(f"{str(mean1)}/100", style="bold green", justify="center")
                elif score_val1 >= 50:
                    mean_text1 = Text(f"{str(mean1)}/100", style="bold yellow", justify="center")
                else:
                    mean_text1 = Text(f"{str(mean1)}/100", style="bold red", justify="center")
            except (TypeError, ValueError):
                mean_text1 = Text(str(mean1), style="dim", justify="center")

            try:
                score_val2 = float(mean2)
                if score_val2 >= 65:
                    mean_text2 = Text(f"{str(mean2)}/100", style="bold green", justify="center")
                elif score_val2 >= 50:
                    mean_text2 = Text(f"{str(mean2)}/100", style="bold yellow", justify="center")
                else:
                    mean_text2 = Text(f"{str(mean2)}/100", style="bold red", justify="center")
            except (TypeError, ValueError):
                mean_text2 = Text(str(mean2), style="dim", justify="center")

            outer.add_row(name, mean_text1, trend_text1, mean_text2, trend_text2)

        console.print(Padding(outer, (0, 0)))
        if score_count1 != 0:
            average_score1 = average_score1/score_count1
        else:
            average_score1 = "No Data"
        
        if score_count2 != 0:
            average_score2 = average_score2/score_count2
        else:
            average_score2 = "No Data"

        # Define winner
        if average_score1 > average_score2:
            score_winner = business1_name
        elif average_score2 > average_score1:
            score_winner = business2_name
        else:
            score_winner = "Draw"
        
        if average_trend1 == "No Data" and average_trend2 != "No Data" and average_trend2 > 0:
            trend_winner = business2_name
        elif average_trend1 == "No Data" and average_trend2 != "No Data" and average_trend2 <= 0:
            trend_winner = "No Data"
        elif average_trend2 == "No Data" and average_trend1 != "No Data" and average_trend1 > 0:
            trend_winner = business1_name
        elif average_trend2 == "No Data" and average_trend1 != "No Data" and average_trend1 <= 0:
            trend_winner = "No Data"
        elif average_trend1 == "No Data" and average_trend2 == "No Data":
            trend_winner = "No Data"
        elif average_trend1 > average_trend2:
            trend_winner = business1_name
        elif average_trend2 > average_trend1:
            trend_winner = business2_name
        else:
            trend_winner = "Draw"

        if reviews_count1 > reviews_count2:
            volume_winner = business1_name
        elif reviews_count2 > reviews_count1:
            volume_winner = business2_name
        else:
            volume_winner = "Draw"

        console.print()
        console.print(Padding("[dim]* Trend reflects the change in sentiment between the most recent week/month in the selected period and the week/month immediately preceding it[/dim]", (0, 4)))
        
        console.print()
        
        hour_unit = "hour" if engine1.time_delta_hours == 1 else "hours"
        hour_unit2 = "hour" if engine2.time_delta_hours == 1 else "hours"

        if engine1.category_alert_status:
            alert_lines1 = Text()
            alert_lines1.append(f"🚨  CATEGORY ALERT FOR {business1_name}\n\n", style="bold red")
            for category in engine1.category_flags.keys():
                if engine1.category_flags[category] > 0:
                    customer_unit = "customer" if engine1.category_flags[category] == 1 else "customers"
                    alert_lines1.append(f"{engine1.category_flags[category]} {customer_unit} reported ", style="red")
                    alert_lines1.append(f"{category}", style="bold red")
                    alert_lines1.append(f" issues within last {engine1.time_delta_hours} {hour_unit}\n", style="red")
            panel1 = Panel(alert_lines1, border_style="bold red", box=box.HEAVY, width=75)
        elif engine1.general_alert_status:
            complaint_unit = "complaint" if engine1.review_count == 1 else "complaints"
            alert_lines1 = Text()
            alert_lines1.append(f"🚨  GENERAL ALERT FOR {business1_name}\n\n", style="bold yellow")
            alert_lines1.append(f"General sentiment is dropping rapidly. {engine1.review_count} unrelated {complaint_unit} detected during last {engine1.time_delta_hours} {hour_unit}.", style="yellow")
            panel1 = Panel(alert_lines1, border_style="bold yellow", box=box.HEAVY, width=75)
        else:
            panel1 = Panel(Text(f"✅  No alerts detected for {business1_name} within last {engine1.time_delta_hours} hours", style="bold green"), border_style="green", box=box.ROUNDED, width=75)

        if engine2.category_alert_status:
            alert_lines2 = Text()
            alert_lines2.append(f"🚨  CATEGORY ALERT FOR {business2_name}\n\n", style="bold red")
            for category in engine2.category_flags.keys():
                if engine2.category_flags[category] > 0:
                    customer_unit = "customer" if engine2.category_flags[category] == 1 else "customers"
                    alert_lines2.append(f"{engine2.category_flags[category]} {customer_unit} reported ", style="red")
                    alert_lines2.append(f"{category}", style="bold red")
                    alert_lines2.append(f" issues within last {engine2.time_delta_hours} {hour_unit2}\n", style="red")
            panel2 = Panel(alert_lines2, border_style="bold red", box=box.HEAVY, width=75)
        elif engine2.general_alert_status:
            complaint_unit = "complaint" if engine2.review_count == 1 else "complaints"
            alert_lines2 = Text()
            alert_lines2.append(f"🚨  GENERAL ALERT FOR {business2_name}\n\n", style="bold yellow")
            alert_lines2.append(f"General sentiment is dropping rapidly. {engine2.review_count} unrelated {complaint_unit} detected during last {engine2.time_delta_hours} {hour_unit2}.", style="yellow")
            panel2 = Panel(alert_lines2, border_style="bold yellow", box=box.HEAVY, width=75)
        else:
            panel2 = Panel(Text(f"✅  No alerts detected for {business2_name} within last {engine2.time_delta_hours} hours", style="bold green"), border_style="green", box=box.ROUNDED, width=75)

        console.print(Columns([panel1, panel2], equal=True))

        console.print()
        console.print(Rule(style="bright_cyan"))
        console.print()

        result_table = Table(box=box.HEAVY, border_style="bright_cyan", show_header=False, expand=False)
        result_table.add_column(justify="center")

        if average_score1 >= 65:
            score_style1 = "bold green"
        elif average_score1 >= 50:
            score_style1 = "bold yellow"
        else:
            score_style1 = "bold red"
        if average_score2 >= 65:
            score_style2 = "bold green"
        elif average_score2 >= 50:
            score_style2 = "bold yellow"
        else:
            score_style2 = "bold red"

        if average_trend1 == "No Data":
            trend_style1 = "dim"
            trend_arrow1 = ""
            trend_label1 = ""
        elif average_trend1 >= 0.1:
            trend_style1 = "bold green"
            trend_arrow1 = "↑"
            trend_label1 = "Improving"
        elif average_trend1 <= -0.1:
            trend_style1 = "bold red"
            trend_arrow1 = "↓"
            trend_label1 = "Declining"
        else:
            trend_style1 = "bold yellow"
            trend_arrow1 = "→"
            trend_label1 = "Stable"
        if average_trend2 == "No Data":
            trend_style2 = "dim"
            trend_arrow2 = ""
            trend_label2 = ""
        elif average_trend2 >= 0.1:
            trend_style2 = "bold green"
            trend_arrow2 = "↑"
            trend_label2 = "Improving"
        elif average_trend2 <= -0.1:
            trend_style2 = "bold red"
            trend_arrow2 = "↓"
            trend_label2 = "Declining"
        else:
            trend_style2 = "bold yellow"
            trend_arrow2 = "→"
            trend_label2 = "Stable"

        score_text = Text(justify="left")
        
        score_text.append(f"{business1_name}\n", style="bold")
        score_text.append(f"Overall Score: {int(average_score1)}/100\n", style=f"bold {score_style1} reverse" if average_score1 < 50 else f"bold {score_style1}") 
        if average_trend1 != "No Data":
            score_text.append(f"Overall Trend: {trend_arrow1} {average_trend1:+.1f} ({trend_label1})", style=trend_style1)
        else:
            score_text.append(f"Overall Trend: {average_trend1}", style=trend_style1)

        score_text.append(f"\n\n{business2_name}\n", style="bold")
        score_text.append(f"Overall Score: {int(average_score2)}/100\n", style=f"bold {score_style2} reverse" if average_score2 < 50 else f"bold {score_style2}") 
        if average_trend2 != "No Data":
            score_text.append(f"Overall Trend: {trend_arrow2} {average_trend2:+.1f} ({trend_label2})", style=trend_style2)
        else:
            score_text.append(f"Overall Trend: {average_trend2}", style=trend_style2)

        score_text.append("\n\n────────────────────────────────────────\n", style="bold bright_cyan")
        
        score_text.append(f"\n🏆 SCORE WINNER: {score_winner}", style="bold")
        score_text.append(f"\n⚡ TREND WINNER: {trend_winner}", style="bold")
        score_text.append(f"\n📊 REVIEWS VOLUME WINNER: {volume_winner}", style="bold")

        console.print(Panel(
            score_text,
            title="[bold bright_cyan] STARLYTICS BATTLE REPORT SUMMARY [/bold bright_cyan]",
            subtitle=f"[bold white]{business1_name} & {business2_name}[/bold white]",
            border_style="bright_cyan",
            box=box.ROUNDED,
            width=46,
            padding=(1, 2),
        ), justify="center")
        console.print()

        console.print(Rule(style="bright_cyan"))

    def check_for_alerts(self, all_reviews):
        self.all_reviews = all_reviews
        self.time_delta = datetime.timedelta(hours=self.time_delta_hours)
        now_time  = datetime.datetime.now()
        in_range_date = now_time-self.time_delta

        self.review_count = 0
        self.category_flags = {"Operational Efficiency": 0, "Value Proposition": 0, "Physical Environment": 0, "Product/Offering": 0, "Other": 0}
        category_flag = 0
        for review in self.all_reviews:
            if review.timestamp >= in_range_date:
                general_flag = 0
                for category_sentiment in review.sentiment.keys():
                    if review.sentiment[category_sentiment] < self.sentiment_threshold:
                        self.category_flags[category_sentiment] += 1
                        general_flag = 1
                        if self.category_flags[category_sentiment] > self.review_count_category_threshold:
                            category_flag = 1
                if general_flag == 1:
                    self.review_count += 1
            else:
                break
    
        if self.review_count > self.review_count_general_threshold:
            self.general_alert_status = True
        else:
            self.general_alert_status = False

        if category_flag == 1:
            self.category_alert_status = True
        else:
            self.category_alert_status = False
    
    def calculate_trends(self, all_reviews):
        self.all_reviews = all_reviews
        self.last_review_date = self.all_reviews[0].timestamp
        self.first_review_date = self.all_reviews[len(self.all_reviews)-1].timestamp
        timespan = self.last_review_date-self.first_review_date
        week = datetime.timedelta(days=7)
        month = datetime.timedelta(days=30)

        self.week_trend_flag = False
        self.month_trend_flag = False

        if week < timespan <= month:
            self.week_trend_flag = True
            last_review_week = self.last_review_date.isocalendar()[1]
            week_ago = last_review_week-1
            last_week_sentiment = {"Operational Efficiency": [], "Value Proposition": [], "Physical Environment": [], "Product/Offering": [], "Other": []}
            week_ago_sentiment = {"Operational Efficiency": [], "Value Proposition": [], "Physical Environment": [], "Product/Offering": [], "Other": []}
            for review in self.all_reviews:
                if review.timestamp.isocalendar()[1] == last_review_week:
                    for key in review.sentiment.keys():
                        last_week_sentiment[key].append(review.sentiment[key])
                elif review.timestamp.isocalendar()[1] == week_ago:
                    for key in review.sentiment.keys():
                        week_ago_sentiment[key].append(review.sentiment[key])
                else:
                    break
            
            flag = 0
            for key in last_week_sentiment.keys():
                if len(last_week_sentiment[key]) != 0 and len(week_ago_sentiment[key]) != 0:
                    last_week_sentiment[key] = round(statistics.mean(last_week_sentiment[key]), 2)
                    week_ago_sentiment[key] = round(statistics.mean(week_ago_sentiment[key]), 2)
                else:
                    last_week_sentiment[key] = "No Data"
                
            if last_week_sentiment["Operational Efficiency"] != "No Data":    
                self.oe_trend = last_week_sentiment["Operational Efficiency"]-week_ago_sentiment["Operational Efficiency"]
            else: 
                self.oe_trend = "No Data"
            if last_week_sentiment["Value Proposition"] != "No Data":  
                self.vp_trend = last_week_sentiment["Value Proposition"]-week_ago_sentiment["Value Proposition"]
            else: 
                self.vp_trend = "No Data"
            if last_week_sentiment["Physical Environment"] != "No Data":  
                self.pe_trend = last_week_sentiment["Physical Environment"]-week_ago_sentiment["Physical Environment"]
            else: 
                self.pe_trend = "No Data"
            if last_week_sentiment["Product/Offering"] != "No Data":  
                self.po_trend = last_week_sentiment["Product/Offering"]-week_ago_sentiment["Product/Offering"]
            else: 
                self.po_trend = "No Data"
            if last_week_sentiment["Other"] != "No Data":  
                self.other_trend = last_week_sentiment["Other"]-week_ago_sentiment["Other"]
            else:
                self.other_trend = "No Data"
        elif timespan > month:
            self.month_trend_flag = True
            self.last_month_review_date = self.last_review_date.month
            self.previous_month_review_date = self.last_month_review_date - 1
            last_month_sentiment = {"Operational Efficiency": [], "Value Proposition": [], "Physical Environment": [], "Product/Offering": [], "Other": []}
            month_ago_sentiment = {"Operational Efficiency": [], "Value Proposition": [], "Physical Environment": [], "Product/Offering": [], "Other": []}
            for review in self.all_reviews:
                if review.timestamp.month == self.last_month_review_date:
                    for key in review.sentiment.keys():
                        last_month_sentiment[key].append(review.sentiment[key])
                elif review.timestamp.month == self.previous_month_review_date:
                    for key in review.sentiment.keys():
                        month_ago_sentiment[key].append(review.sentiment[key])
                else:
                    break
            
            flag = 0
            for key in last_month_sentiment.keys():
                if len(last_month_sentiment[key]) != 0 and len(month_ago_sentiment[key]) != 0:
                    last_month_sentiment[key] = round(statistics.mean(last_month_sentiment[key]), 2)
                    month_ago_sentiment[key] = round(statistics.mean(month_ago_sentiment[key]), 2)
                else:
                    last_month_sentiment[key] = "No Data"
                
            if last_month_sentiment["Operational Efficiency"] != "No Data":    
                self.oe_trend = last_month_sentiment["Operational Efficiency"]-month_ago_sentiment["Operational Efficiency"]
            else: 
                self.oe_trend = "No Data"
            if last_month_sentiment["Value Proposition"] != "No Data":  
                self.vp_trend = last_month_sentiment["Value Proposition"]-month_ago_sentiment["Value Proposition"]
            else: 
                self.vp_trend = "No Data"
            if last_month_sentiment["Physical Environment"] != "No Data":  
                self.pe_trend = last_month_sentiment["Physical Environment"]-month_ago_sentiment["Physical Environment"]
            else: 
                self.pe_trend = "No Data"
            if last_month_sentiment["Product/Offering"] != "No Data":  
                self.po_trend = last_month_sentiment["Product/Offering"]-month_ago_sentiment["Product/Offering"]
            else: 
                self.po_trend = "No Data"
            if last_month_sentiment["Other"] != "No Data":  
                self.other_trend = last_month_sentiment["Other"]-month_ago_sentiment["Other"]
            else:
                self.other_trend = "No Data"
    
    def process_keywords(self, all_reviews):
        self.oe_positive_kw = Counter()
        self.oe_negative_kw = Counter()

        self.vp_positive_kw = Counter()
        self.vp_negative_kw = Counter()

        self.pe_positive_kw = Counter()
        self.pe_negative_kw = Counter()

        self.po_positive_kw = Counter()
        self.po_negative_kw = Counter()

        self.other_positive_kw = Counter()
        self.other_negative_kw = Counter()

        for review in all_reviews:
            positive_keywords = review.positive_keywords
            negative_keywords = review.negative_keywords
            for category in positive_keywords.keys():
                if category == "Operational Efficiency":
                    self.oe_positive_kw += positive_keywords[category]
                elif category == "Value Proposition":
                    self.vp_positive_kw += positive_keywords[category]
                elif category == "Physical Environment":
                    self.pe_positive_kw += positive_keywords[category]
                elif category == "Product/Offering":
                    self.po_positive_kw += positive_keywords[category]
                else:
                    self.other_positive_kw += positive_keywords[category]
            
            for category in negative_keywords.keys():
                if category == "Operational Efficiency":
                    self.oe_negative_kw += negative_keywords[category]
                elif category == "Value Proposition":
                    self.vp_negative_kw += negative_keywords[category]
                elif category == "Physical Environment":
                    self.pe_negative_kw += negative_keywords[category]
                elif category == "Product/Offering":
                    self.po_negative_kw += negative_keywords[category]
                else:
                    self.other_negative_kw += negative_keywords[category]
        
        self.oe_positive_kw = self.oe_positive_kw.most_common(10)
        self.oe_negative_kw = self.oe_negative_kw.most_common(10)
        
        self.vp_positive_kw = self.vp_positive_kw.most_common(10)
        self.vp_negative_kw = self.vp_negative_kw.most_common(10)
        
        self.pe_positive_kw = self.pe_positive_kw.most_common(10)
        self.pe_negative_kw = self.pe_negative_kw.most_common(10)
        
        self.po_positive_kw = self.po_positive_kw.most_common(10)
        self.po_negative_kw = self.po_negative_kw.most_common(10)

        self.other_positive_kw = self.other_positive_kw.most_common(10)
        self.other_negative_kw = self.other_negative_kw.most_common(10)

        # print(self.oe_positive_kw, self.oe_negative_kw)
        # print()
        # print(self.vp_positive_kw, self.vp_negative_kw)
        # print()
        # print(self.pe_positive_kw, self.pe_negative_kw)
        # print()
        # print(self.po_positive_kw, self.po_negative_kw)
        # print()
        # print(self.other_positive_kw, self.other_negative_kw)
        # print()
    
    def generate_ai_insight(self):
        try:
            client = genai.Client()
            key_words = "Operational Efficiency Positive Keywords: "
            for kw in self.oe_positive_kw:
                key_words += f"{kw[0]}({kw[1]}x), "
            
            key_words += "\nOperational Efficiency Negative Keywords: "
            for kw in self.oe_negative_kw:
                key_words += f"{kw[0]}({kw[1]}x), "

            key_words += "\n\nValue Proposition Positive Keywords: "
            for kw in self.vp_positive_kw:
                key_words += f"{kw[0]}({kw[1]}x), "
            
            key_words += "\nValue Proposition Negative Keywords: "
            for kw in self.vp_negative_kw:
                key_words += f"{kw[0]}({kw[1]}x), "

            key_words += "\n\nPhysical Environment Positive Keywords: "
            for kw in self.pe_positive_kw:
                key_words += f"{kw[0]}({kw[1]}x), "
            
            key_words += "\nPhysical Environment Negative Keywords: "
            for kw in self.pe_negative_kw:
                key_words += f"{kw[0]}({kw[1]}x), "

            key_words += "\n\nProduct/Offering Positive Keywords: "
            for kw in self.po_positive_kw:
                key_words += f"{kw[0]}({kw[1]}x), "
            
            key_words += "\nProduct/Offering Negative Keywords: "
            for kw in self.po_negative_kw:
                key_words += f"{kw[0]}({kw[1]}x), "

            key_words += "\n\nOther Category Positive Keywords: "
            for kw in self.other_positive_kw:
                key_words += f"{kw[0]}({kw[1]}x), "
            
            key_words += "\nOther Category Negative Keywords: "
            for kw in self.other_negative_kw:
                key_words += f"{kw[0]}({kw[1]}x), "

            scores = ""
            for name, mean, trend_text in [
                ("Operational Efficiency", self.oe_mean, self.oe_trend_text),
                ("Value Proposition", self.vp_mean, self.vp_trend_text),
                ("Physical Environment", self.pe_mean, self.pe_trend_text),
                ("Product/Offering", self.po_mean, self.po_trend_text),
                ("Other", self.other_mean, self.other_trend_text),
            ]:
                scores += f"{name}: {mean} {trend_text}\n"
                
            prompt = f"""You are a business analytics expert. Analyze the following customer review data and provide insights. Your task is to analyze aggregated keyword frequency data and write a fluid, professional strategic report.
    
    SCORES AND TRENDS:
    {scores}
    TOP KEYWORDS FROM REVIEWS:
    {key_words}
    
    Your response must follow this exact structure with these exact section headers:
    
    CATEGORY ANALYSIS:
    For each category that has data, write 1-2 sentences explaining what customers are saying, what is working and what is not, referencing the actual keywords.
    
    ACTIONABLE RECOMMENDATIONS:
    List 3-5 specific, concrete actions the business should take based on the data. Reference specific keywords (e.g. "parking complaints suggest adding a valet service or partnering with a nearby lot"). Be direct and practical.
    
    STRATEGY SUMMARY:
    Write 2-3 sentences giving an overall strategic verdict. What is the business doing well, what is hurting them, and what is the single most important thing to fix first.
    
    Be direct, specific, and use the actual keyword data. Do not be generic. 
    Do not use markdown formatting of any kind — no asterisks, no bold, no bullet symbols.
    Do not assume the type of business — analyze only what the data shows.
    Keep each category analysis to 2 short sentences maximum.
    In the strategy summary, name the single highest-volume negative keyword explicitly and center the verdict around it.

    STYLE & FORMATTING RULES:
    1. SMOOTH INTEGRATION: Do not just list keywords separated by commas (e.g., Avoid: 'Fix the "dirty," "messy," and "cold" room'). Instead, weave them naturally into professional business prose (e.g., Prefer: 'Address physical environment friction points by focusing on cleanliness and regulating room temperature').
    2. JUDICIOUS QUOTES: Do not wrap every single keyword in quotation marks. Use quotes ONLY when highlighting a critical, high-frequency customer sentiment trend or direct vocabulary pattern. 
    3. GROUNDED STRATEGY: Base every insight strictly on the provided data, but write your recommendations as actionable business directives rather than text-matching checklists.
    4. Your output MUST use highly structured Markdown so it renders beautifully in a terminal UI. Use markdown headers (###) for each main category.
    5. DO NOT write long paragraphs. Break categories down into clean, indented bullet points (-). Use bolding for category titles and don't forget : after them. every category header must use the Heading 3 (###) syntax, and the category name itself MUST be wrapped in single backticks (code syntax). This forces the terminal to render the title in yellow. For the "ACTIONABLE RECOMMENDATIONS" section, you MUST use a standard Markdown numbered list (e.g., 1., 2., 3., 4.). Do not use hyphens, asterisks, or bullet points here.
    6. Use italic text (*keyword*) to make high-frequency keywords stand out.
    7. Separate the main sections using markdown horizontal rules (---).
    """     
            try:
                with console.status("[bold cyan]Preparing AI Keyword Analysis & Strategy...[/] ", spinner="aesthetic"):
                    self.response = client.models.generate_content(
                        model=self.ai_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.3),
                        
                    )
                console.print("✅ [bold green]Analysis Complete![/]\n")
                console.print(Rule(style="bright_cyan"))
                console.print(Text(f"🤖 AI KEYWORD ANALYSIS & STRATEGY", style="bold bright_cyan"), justify="center")
                console.print(Rule(style="bright_cyan"))
                console.print()
                md = Markdown(self.response.text)
                console.print(md)
                console.print()
                console.print(Rule(style="bright_cyan"))
            except genai.errors.ServerError:
                error_message = (
                    "[bold red]❌ AI KEYWORD ANALYSIS FAILED[/]\n\n"
                    "The Gemini (Starlytics AI engine) servers are currently experiencing a heavy traffic spike\n"
                    "(503 Service Unavailable). Your data is safe, but the system"
                    "cannot process the request at this exact second.\n\n"
                    "[bold cyan]RECOMMENDED ACTIONS:[/]\n"
                    "1. Wait 10-15 seconds and re-run report.\n"
                    "2. If congestion persists, go to Starlytics Settings and change the AI model\n"
                )
                
                console.print(
                    Panel(
                        error_message, 
                        border_style="bold red", 
                        expand=False,
                        padding=(1, 2)
                    )
                )
            except genai.errors.ClientError as error:
                if error.code == 400:
                    console.print(Rule(style="bright_cyan"))
                    error_message = Text()  
                    error_message.append("Your Gemini API Key is invalid.\n\nGo to Starlytics Settings, choose \"Set Gemini API Key\" (7th option), and enter valid Google Studio Gemini API Key.\n\nError Code: 400")
                    console.print(
                        Panel(
                        error_message, 
                        border_style="bold red", 
                        title="❌ INVALID API KEY CONFIGURATION (400)", 
                        padding=(1, 2)
                        )   
                    )
                elif error.code == 429:
                    console.print(Rule(style="bright_cyan"))
                    error_message = Text()  
                    error_message.append("Your daily free tier quota for current Gemini API Key has been reached.\n")
                    error_message.append("Please swap your API key via option 7 in Starlytics Settings or wait for the daily window to reset.\n\n")
                    error_message.append("💡 Developer Tip: ", style="bold green")
                    error_message.append(
                    "If you exhaust your daily limit, you can create a fresh API token using a secondary Google account in Google AI Studio and paste it in Starlytics Settings to bypass the restriction instantly without restarting Starlytics.\n\n", 
                    style="white"
                    )
                    error_message.append("Eror Code: 429 ")
                    
                    console.print(
                        Panel(
                        error_message, 
                        border_style="bold yellow", 
                        title="⚠️  API RATE LIMIT EXHAUSTED (429)", 
                        padding=(1, 2)
                        )   
                    )
                else:
                    console.print(Rule(style="bright_cyan"))
                    error_message = Text()  
                    error_message.append("Contact the developer with your problem")
                    
                    console.print(
                        Panel(
                        error_message, 
                        border_style="bold yellow", 
                        title="❌ Application Error", 
                        padding=(1, 2)
                        )   
                    )
        except ValueError:
            console.print(Rule(style="bright_cyan"))
            error_message = Text()
            error_message.append("⚠️  Starlytics requires a valid Gemini API key to generate AI keyword analysis and strategy.\n\n", style="white")
            
            error_message.append("📋 STEP-BY-STEP SETUP GUIDE:\n\n", style="bold cyan")
            
            error_message.append("1. Get a Free Key:\n", style="bold white")
            error_message.append("Go to Google AI Studio at ", style="white")
            error_message.append("https://aistudio.google.com/\n\n", style="bold underline bright_blue")
            error_message.append(f"2. Click \"Get API Key\" button (in the bottom-left corner)\n\n", style="bold white")
            error_message.append(f"3. Click \"Create API Key\" button (in the top right corner) and create key\n\n", style="bold white")
            error_message.append(f"4. Copy API key, go to Starlytics Settings (3rd option), choose \"Set Gemini API Key\" (7th Option), and paste API Key", style="bold white")
            error_message.append(f"\n\n5. Congrats! Your Gemini API key is set. Now, you can rerun report with AI keyword analysis and strategy available", style="bold white")
            
            console.print(
                Panel(
                    error_message, 
                    border_style="bold yellow", 
                    title="GEMINI API KEY MISSING", 
                    padding=(1, 2)
                )
            )
    
    def generate_competitive_ai_insight(self, engine1, engine2, business_name1, business_name2):
        try:
            client = genai.Client()
            key_words1 = f"Business {business_name1} Operational Efficiency Positive Keywords: "
            for kw in engine1.oe_positive_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "
            
            key_words1 += f"\nBusiness {business_name1} Operational Efficiency Negative Keywords: "
            for kw in engine1.oe_negative_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "

            key_words1 += f"\n\nBusiness {business_name1} Value Proposition Positive Keywords: "
            for kw in engine1.vp_positive_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "
            
            key_words1 += f"\nBusiness {business_name1} Value Proposition Negative Keywords: "
            for kw in engine1.vp_negative_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "

            key_words1 += f"\n\nBusiness {business_name1} Physical Environment Positive Keywords: "
            for kw in engine1.pe_positive_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "
            
            key_words1 += f"\nBusiness {business_name1} Physical Environment Negative Keywords: "
            for kw in engine1.pe_negative_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "

            key_words1 += f"\n\nBusiness {business_name1} Product/Offering Positive Keywords: "
            for kw in engine1.po_positive_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "
            
            key_words1 += f"\nBusiness {business_name1} Product/Offering Negative Keywords: "
            for kw in engine1.po_negative_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "

            key_words1 += f"\n\nBusiness {business_name1} Other Category Positive Keywords: "
            for kw in engine1.other_positive_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "
            
            key_words1 += f"\nBusiness {business_name1} Other Category Negative Keywords: "
            for kw in engine1.other_negative_kw:
                key_words1 += f"{kw[0]}({kw[1]}x), "


            key_words2 = f"Business {business_name2} Operational Efficiency Positive Keywords: "
            for kw in engine2.oe_positive_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "
            
            key_words2 += f"\nBusiness {business_name2} Operational Efficiency Negative Keywords: "
            for kw in engine2.oe_negative_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "

            key_words2 += f"\n\nBusiness {business_name2} Value Proposition Positive Keywords: "
            for kw in engine2.vp_positive_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "
            
            key_words2 += f"\nBusiness {business_name2} Value Proposition Negative Keywords: "
            for kw in engine2.vp_negative_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "

            key_words2 += f"\n\nBusiness {business_name2} Physical Environment Positive Keywords: "
            for kw in engine2.pe_positive_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "
            
            key_words2 += f"\nBusiness {business_name2} Physical Environment Negative Keywords: "
            for kw in engine2.pe_negative_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "

            key_words2 += f"\n\nBusiness {business_name2} Product/Offering Positive Keywords: "
            for kw in engine2.po_positive_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "
            
            key_words2 += f"\nBusiness {business_name2} Product/Offering Negative Keywords: "
            for kw in engine2.po_negative_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "

            key_words2 += f"\n\nBusiness {business_name2} Other Category Positive Keywords: "
            for kw in engine2.other_positive_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "
            
            key_words2 += f"\nBusiness {business_name2} Other Category Negative Keywords: "
            for kw in engine2.other_negative_kw:
                key_words2 += f"{kw[0]}({kw[1]}x), "

            scores1 = ""
            for name, mean, trend_text in [
                ("Operational Efficiency", engine1.oe_mean, engine1.oe_trend_text),
                ("Value Proposition", engine1.vp_mean, engine1.vp_trend_text),
                ("Physical Environment", engine1.pe_mean, engine1.pe_trend_text),
                ("Product/Offering", engine1.po_mean, engine1.po_trend_text),
                ("Other", engine1.other_mean, engine1.other_trend_text),
            ]:
                scores1 += f"{name}: {mean} {trend_text}\n"
            
            scores2 = ""
            for name, mean, trend_text in [
                ("Operational Efficiency", engine2.oe_mean, engine2.oe_trend_text),
                ("Value Proposition", engine2.vp_mean, engine2.vp_trend_text),
                ("Physical Environment", engine2.pe_mean, engine2.pe_trend_text),
                ("Product/Offering", engine2.po_mean, engine2.po_trend_text),
                ("Other", engine2.other_mean, engine2.other_trend_text),
            ]:
                scores2 += f"{name}: {mean} {trend_text}\n"
                
            prompt = f"""You are a business analytics expert. Your task is to analyze customer review keyword data for two competing businesses and write a competitive intelligence report.

BUSINESS 1: {business_name1}
SCORES AND TRENDS:
{scores1}
TOP KEYWORDS FROM REVIEWS:
{key_words1}

BUSINESS 2: {business_name2}
SCORES AND TRENDS:
{scores2}
TOP KEYWORDS FROM REVIEWS:
{key_words2}

Your response must follow this exact structure with these exact section headers:

CATEGORY ANALYSIS:
For each category that has data for both businesses, write 2-3 sentences directly comparing them. Who is winning this category and why. Reference actual keyword differences between the two. If one business has no data for a category, note that.

COMPETITIVE ADVANTAGES:
For each business, write 2-3 sentences identifying what it does measurably better than the other based strictly on keyword evidence. Name the specific category and keywords that prove the advantage.

CRITICAL WEAKNESSES:
For each business, identify its single biggest vulnerability that the competitor could exploit. Be specific — name the category, the dominant negative keywords, and why it matters competitively.

STRATEGY SUMMARY:
2-3 sentences maximum. Name the overall winner and why. Then give each business one concrete directive for the next 30 days to either close the gap or extend the lead.

Be direct, specific, and use the actual keyword data. Do not be generic. 
Do not use markdown formatting of any kind — no asterisks, no bold, no bullet symbols.
Do not assume the type of business — analyze only what the data shows.
Keep each category analysis to 2 short sentences maximum.
In the strategy summary, name the single highest-volume negative keyword explicitly and center the verdict around it.


STYLE AND FORMATTING RULES:
1. SMOOTH INTEGRATION: Do not just list keywords separated by commas (e.g., Avoid: 'Fix the "dirty," "messy," and "cold" room'). Instead, weave them naturally into professional business prose (e.g., Prefer: 'Address physical environment friction points by focusing on cleanliness and regulating room temperature').
2. JUDICIOUS QUOTES: Do not wrap every single keyword in quotation marks. Use quotes ONLY when highlighting a critical, high-frequency customer sentiment trend or direct vocabulary pattern. 
3. Your output MUST use highly structured Markdown so it renders beautifully in a terminal UI. Use markdown headers (###) for each main category.
4. DO NOT write long paragraphs. Break categories down into clean, indented bullet points (-). Use bolding for category titles and don't forget : after them. every category header must use the Heading 3 (###) syntax, and the category name itself MUST be wrapped in single backticks (code syntax). This forces the terminal to render the title in yellow. For the "ACTIONABLE RECOMMENDATIONS" section, you MUST use a standard Markdown numbered list (e.g., 1., 2., 3., 4.). Do not use hyphens, asterisks, or bullet points here.
5. Use italic text (*keyword*) to make high-frequency keywords stand out.
6. Separate the main sections using markdown horizontal rules (---). 
7. DENSITY & SCANNABILITY: Avoid long prose or blocks of narrative paragraphs. Break every category down into punchy, immediate bullet points.
8. STRUCTURE FORMULA: For Category Analysis, start each point with a clear trend statement, followed by precise metric callouts (e.g., "77x vs. 47x"). Use the '➔' symbol or bold text to separate the metrics from the strategic takeaway.
9. DATA SPARSITY: If a category contains no data for either business (such as the "Other" category), do not dedicate a large empty section to it. Omit it or place it in a single concise note.
"""
            try:
                with console.status("[bold cyan]Preparing AI Keyword Analysis & Strategy...[/] ", spinner="aesthetic"):
                    self.response = client.models.generate_content(
                        model=self.ai_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(temperature=0.3),
                        
                    )
                console.print("✅ [bold green]Analysis Complete![/]\n")
                console.print(Rule(style="bright_cyan"))
                console.print(Text(f"🤖 AI KEYWORD CROSS-ANALYSIS ", style="bold bright_cyan"), justify="center")
                console.print(Rule(style="bright_cyan"))
                console.print()
                md = Markdown(self.response.text)
                console.print(md)
                console.print()
                console.print(Rule(style="bright_cyan"))
            except genai.errors.ServerError:
                error_message = (
                    "[bold red]❌ AI COMPETITIVE KEYWORD CROSS-ANALYSIS FAILED[/]\n\n"
                    "The Gemini (Starlytics AI engine) servers are currently experiencing a heavy traffic spike\n"
                    "(503 Service Unavailable). Your data is safe, but the system"
                    "cannot process the request at this exact second.\n\n"
                    "[bold cyan]RECOMMENDED ACTIONS:[/]\n"
                    "1. Wait 10-15 seconds and re-run report.\n"
                    "2. If congestion persists, go to Starlytics Settings and change the AI model\n"
                )
                
                console.print(
                    Panel(
                        error_message, 
                        border_style="bold red", 
                        expand=False,
                        padding=(1, 2)
                    )
                )
            except genai.errors.ClientError as error:
                if error.code == 400:
                    console.print(Rule(style="bright_cyan"))
                    error_message = Text()  
                    error_message.append("Your Gemini API Key is invalid.\n\nGo to Starlytics Settings, choose \"Set Gemini API Key\" (7th option), and enter valid Google Studio Gemini API Key.\n\nError Code: 400")
                    console.print(
                        Panel(
                        error_message, 
                        border_style="bold red", 
                        title="❌ INVALID API KEY CONFIGURATION (400)", 
                        padding=(1, 2)
                        )   
                    )
                elif error.code == 429:
                    console.print(Rule(style="bright_cyan"))
                    error_message = Text()  
                    error_message.append("Your daily free tier quota for current Gemini API Key has been reached.\n")
                    error_message.append("Please swap your API key via option 7 in Starlytics Settings or wait for the daily window to reset.\n\n")
                    error_message.append("💡 Developer Tip: ", style="bold green")
                    error_message.append(
                    "If you exhaust your daily limit, you can create a fresh API token using a secondary Google account in Google AI Studio and paste it in Starlytics Settings to bypass the restriction instantly without restarting Starlytics.\n\n", 
                    style="white"
                    )
                    error_message.append("Eror Code: 429 ")
                    
                    console.print(
                        Panel(
                        error_message, 
                        border_style="bold yellow", 
                        title="⚠️  API RATE LIMIT EXHAUSTED (429)", 
                        padding=(1, 2)
                        )   
                    )
                else:
                    console.print(Rule(style="bright_cyan"))
                    error_message = Text()  
                    error_message.append("Contact the developer with your problem")
                    
                    console.print(
                        Panel(
                        error_message, 
                        border_style="bold yellow", 
                        title="❌ Application Error", 
                        padding=(1, 2)
                        )   
                    )
        except ValueError:
            console.print(Rule(style="bright_cyan"))
            error_message = Text()
            error_message.append("⚠️  Starlytics requires a valid Gemini API key to generate AI keyword analysis and strategy.\n\n", style="white")
            
            error_message.append("📋 STEP-BY-STEP SETUP GUIDE:\n\n", style="bold cyan")
            
            error_message.append("1. Get a Free Key:\n", style="bold white")
            error_message.append("Go to Google AI Studio at ", style="white")
            error_message.append("https://aistudio.google.com/\n\n", style="bold underline bright_blue")
            error_message.append(f"2. Click \"Get API Key\" button (in the bottom-left corner)\n\n", style="bold white")
            error_message.append(f"3. Click \"Create API Key\" button (in the top right corner) and create key\n\n", style="bold white")
            error_message.append(f"4. Copy API key, go to Starlytics Settings (3rd option), choose \"Set Gemini API Key\" (7th Option), and paste API Key", style="bold white")
            error_message.append(f"\n\n5. Congrats! Your Gemini API key is set. Now, you can rerun report with AI keyword analysis and strategy available", style="bold white")
            
            console.print(
                Panel(
                    error_message, 
                    border_style="bold yellow", 
                    title="GEMINI API KEY MISSING", 
                    padding=(1, 2)
                )
            )
