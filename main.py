import datetime
import csv
import re
import statistics
import time
import sys
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from starlytics_engine import StarlyticsEngine
from rich.console import Console
from rich.text import Text
from rich.rule import Rule
from rich.panel import Panel
from rich.prompt import Prompt
from categories_kw import categories_kw
from collections import Counter
from categories_kw import umbrella_words

analyzer = SentimentIntensityAnalyzer()
analyzer = SentimentIntensityAnalyzer()
analyzer.lexicon.update({
        "modern": 2.0, 
        "expensive": -1.5, 
        "too": -2.0, 
        "too long": -2.0, 
        "disinterested": -2.5, 
        "decent": 1.0,
        "broken": -2.5,
})
console = Console()
categories_kw = categories_kw

# mac:
# export GEMINI_API_KEY="api_key"
# windows:
# set GEMINI_API_KEY=api_key

# returns a dictionary with neg, neu, pos, and compound keys
# score = analyzer.polarity_scores(text)

class Review:
    def __init__(self, stars: int, text: str, timestamp: object, category: set={"Uncategorized"}, sentiment: dict={}, positive_keywords: dict={}, negative_keywords: dict={}):
        self.stars = stars
        self.text = text
        self.timestamp = timestamp
        self.category = category
        self.sentiment = sentiment
    
    def __str__(self):
        return f"""
Stars: {self.stars}
Text: {self.text}
Timestamp: {self.timestamp}
Category: {self.category}
Sentiment: {self.sentiment}
        """

engine = StarlyticsEngine()

def main():
    try:
        while True:
            try: 
                menu_text = "[cyan]1[/cyan] ➔ Solo Report\n[cyan]2[/cyan] ➔ Battle Report\n[cyan]3[/cyan] ➔ Settings\n[cyan]4[/cyan] ➔ Exit Program"
            
                console.print(Panel(menu_text, title="[bold bright_cyan] STARLYTICS MENU [/bold bright_cyan]", expand=False, padding=(1, 3)))
                
                mode = Prompt.ask("[bold white]Choose option[/bold white]", choices=["1", "2", "3", "4"])
                if mode == "1":
                    business_name = input("Enter business name: ")
                    period_start, period_end = get_period()  

                    file_name = "mock_reviews.csv"
                    
                    all_reviews, reviews_count = ingestor(period_start, period_end, file_name)

                    with console.status("[bold cyan]Analyzing Reviews...[/] ", spinner="aesthetic"):

                        start_time = time.time()
                        for review in all_reviews:
                            review.category = categorize_review(review)
                            review.sentiment = sentimentize_review(review)
                            review.positive_keywords, review.negative_keywords = get_keywords(review)
                        
                        engine.caculate_category_means(all_reviews, engine)
                        engine.check_for_alerts(all_reviews)
                        engine.calculate_trends(all_reviews)
                        engine.process_keywords(all_reviews)

                        end_time = time.time()
                        total_time = end_time-start_time

                    console.print("✅ [bold green]Analysis Complete![/]\n")
                    engine.generate_report(reviews_count, total_time, business_name)
                    engine.generate_ai_insight()

                    main()
                elif mode == "2":
                    business1_name = input("Enter first business name: ")
                    business2_name = input("Enter second business name: ")
                    period_start, period_end = get_period()

                    file_name1 = "mock_reviews_business1.csv"
                    file_name2 = "mock_reviews_business2.csv"

                    all_reviews1, reviews_count1 = ingestor(period_start, period_end, file_name1)
                    all_reviews2, reviews_count2  = ingestor(period_start, period_end, file_name2)
                    
                    with console.status(f"[bold cyan]Analyzing Reviews for {business1_name}...[/] ", spinner="aesthetic"):
                        start_time1 = time.time()
                        for review in all_reviews1:
                            review.category = categorize_review(review)
                            review.sentiment = sentimentize_review(review)
                            review.positive_keywords, review.negative_keywords = get_keywords(review)
                        
                        engine1 = StarlyticsEngine()

                        engine1.caculate_category_means(all_reviews1, engine)
                        engine1.check_for_alerts(all_reviews1)
                        engine1.calculate_trends(all_reviews1)
                        engine1.process_keywords(all_reviews1)

                        end_time1 = time.time()
                        total_time1 = end_time1-start_time1
                    
                    console.print(f"✅ [bold green]Analysis for {business1_name} Complete![/]\n")

                    with console.status(f"[bold cyan]Analyzing Reviews for {business2_name}...[/] ", spinner="aesthetic"):
                        start_time2 = time.time()
                        for review in all_reviews2:
                            review.category = categorize_review(review)
                            review.sentiment = sentimentize_review(review)
                            review.positive_keywords, review.negative_keywords = get_keywords(review)

                        engine2 = StarlyticsEngine()

                        engine2.caculate_category_means(all_reviews2, engine)
                        engine2.check_for_alerts(all_reviews2)
                        engine2.calculate_trends(all_reviews2)
                        engine2.process_keywords(all_reviews2)

                        end_time2 = time.time()
                        total_time2 = end_time2-start_time2

                    console.print(f"✅ [bold green]Analysis for {business2_name} Complete![/]\n")

                    engine.generate_battle_report(engine1, engine2, reviews_count1, reviews_count2, total_time1, total_time2, business1_name, business2_name)
                    engine.generate_competitive_ai_insight(engine1, engine2, business1_name, business2_name)

                    main()
                elif mode == "3":
                    settings_mode()
                elif mode == "4":
                    sys.exit()
                else:
                    raise ValueError
                break
            except ValueError:
                print("Invalid Input")
    except KeyboardInterrupt:
        sys.exit()

def settings_mode():
    while True:
        try:
            console.print(Rule(style="bright_cyan"))
            
            settings_text = (
                    "[cyan]1[/cyan] ➔ Change Alert Time Window\n"
                    "[cyan]2[/cyan] ➔ Change Alert Sentiment Threshold\n"
                    "[cyan]3[/cyan] ➔ Change General Alert Reviews Number Threshold\n"
                    "[cyan]4[/cyan] ➔ Change Category Alert Reviews Number Threshold\n"
                    "[cyan]5[/cyan] ➔ Recency Weighting Toggle\n"
                    "[cyan]6[/cyan] ➔ Change AI model\n"
                    "[cyan]7[/cyan] ➔ Set Gemini API Key\n"
                    "[cyan]Enter[/cyan] ➔ Exit Settings"
                )
                
            console.print(Panel(
                settings_text, 
                title="[bold bright_cyan] STARLYTICS SETTINGS [/bold bright_cyan]", 
                expand=False, 
                padding=(1, 3)
            ))
            
            option = Prompt.ask(
                "[bold white]Choose option[/bold white]", 
                choices=["1", "2", "3", "4", "5", "6", "7", ""]
            )
        
            if option == "1":
                console.print(Rule(style="bright_cyan"))
                    
                settings_info = Text()
                settings_info.append("How Starlytics Alert System works:\n\n", style="bold yellow")
                settings_info.append(
                    f"If within the past {engine.time_delta_hours} hours there are "
                    f"{engine.review_count_general_threshold} reviews with sentiment below "
                    f"{engine.sentiment_threshold}, Starlytics will raise a General alert.\n\n"
                    f"If within the past {engine.time_delta_hours} hours there are {engine.review_count_category_threshold}+ reviews with sentiment below {engine.sentiment_threshold} within a "
                    f"specific category, Starlytics will raise a Category Alert instead, indicating this category and number of negative reviews.\n\n",
                )
                settings_info.append("Current Alert Time Window: ", style="bold white")
                settings_info.append(f"{engine.time_delta_hours} hours (default: 72 hours)", style="yellow")
                settings_info.append(f"\n\n*Number values can be changed in Starlytics Settings", style="dim")

                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: Alert Time Window [/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                console.print()
                
                while True:
                    try:
                        user_input = input("Enter new timeframe in hours (e.g., 0, 1, 2): ")
                        time_delta_hours = int(user_input)
                        
                        engine.time_delta_hours = time_delta_hours
                        console.print("\n✅ Alert window updated successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Enter a whole number (e.g., 0, 1, 2)\n", style="bold red")
            elif option == "2":
                console.print(Rule(style="bright_cyan"))
                    
                settings_info = Text()
                settings_info.append("How Starlytics Alert System works:\n\n", style="bold yellow")
                settings_info.append(
                    f"If within the past {engine.time_delta_hours} hours there are "
                    f"{engine.review_count_general_threshold} reviews with sentiment below "
                    f"{engine.sentiment_threshold}, Starlytics will raise a General alert.\n\n"
                    f"If within the past {engine.time_delta_hours} hours there are {engine.review_count_category_threshold}+ reviews with sentiment below {engine.sentiment_threshold} within a "
                    f"specific category, Starlytics will raise a Category Alert instead, indicating this category and number of negative reviews.\n\n",
                )
                settings_info.append("Current Alert Sentiment Threshold: ", style="bold white")
                settings_info.append(f"{engine.sentiment_threshold} (default: 15)", style="yellow")
                settings_info.append(f"\n\n*Number values can be changed in Starlytics Settings", style="dim")

                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: Alert Sentiment Threshold s[/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                console.print()
                
                while True:
                    try:
                        user_input = input("Enter new Sentiment Threshold (1-100): ")
                        sentiment_threshold = int(user_input)
                        
                        engine.sentiment_threshold = sentiment_threshold
                        console.print("\n✅ Sentiment Threshold updated successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Enter an integer that is between 1 and 100\n", style="bold red")
            elif option == "3":
                console.print(Rule(style="bright_cyan"))
                    
                settings_info = Text()
                settings_info.append("How Starlytics Alert System works:\n\n", style="bold yellow")
                settings_info.append(
                    f"If within the past {engine.time_delta_hours} hours there are "
                    f"{engine.review_count_general_threshold} reviews with sentiment below "
                    f"{engine.sentiment_threshold}, Starlytics will raise a General alert.\n\n"
                    f"If within the past {engine.time_delta_hours} hours there are {engine.review_count_category_threshold}+ reviews with sentiment below {engine.sentiment_threshold} within a "
                    f"specific category, Starlytics will raise a Category Alert instead, indicating this category and number of negative reviews.\n\n",
                )
                settings_info.append("Current General Alert Reviews Number Threshold: ", style="bold white")
                settings_info.append(f"{engine.review_count_general_threshold} (default: 3)", style="yellow")
                settings_info.append(f"\n\n*Number values can be changed in Starlytics Settings", style="dim")

                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: General Alert Reviews Number Threshold [/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                console.print()
                
                while True:
                    try:
                        user_input = input("Enter new General Alert Reviews Number Threshold (e.g., 0, 1, 2): ")
                        review_count_general_threshold = int(user_input)
                        
                        engine.review_count_general_threshold = review_count_general_threshold
                        console.print("\n✅ General Alert Reviews Number Threshold updated successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Enter a whole number (e.g., 0, 1, 2)\n", style="bold red")
            elif option == "4":
                console.print(Rule(style="bright_cyan"))
                    
                settings_info = Text()
                settings_info.append("How Starlytics Alert System works:\n\n", style="bold yellow")
                settings_info.append(
                    f"If within the past {engine.time_delta_hours} hours there are "
                    f"{engine.review_count_general_threshold} reviews with sentiment below "
                    f"{engine.sentiment_threshold}, Starlytics will raise a General alert.\n\n"
                    f"If within the past {engine.time_delta_hours} hours there are {engine.review_count_category_threshold}+ reviews with sentiment below {engine.sentiment_threshold} within a "
                    f"specific category, Starlytics will raise a Category Alert instead, indicating this category and number of negative reviews.\n\n",
                )
                settings_info.append("Current Category Alert Reviews Number Threshold: ", style="bold white")
                settings_info.append(f"{engine.review_count_category_threshold} (default: 2)", style="yellow")
                settings_info.append(f"\n\n*Number values can be changed in Starlytics Settings", style="dim")

                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: Category Alert Reviews Number Threshold [/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                console.print()
                
                while True:
                    try:
                        user_input = input("Enter new Category Alert Reviews Number Threshold (e.g., 0, 1, 2): ")
                        review_count_category_threshold = int(user_input)
                        
                        engine.review_count_category_threshold = review_count_category_threshold
                        console.print("\n✅ Category Alert Reviews Number Threshold updated successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Enter a whole number (e.g., 0, 1, 2)\n", style="bold red")
            elif option == "5":
                console.print(Rule(style="bright_cyan"))
                    
                settings_info = Text()
                settings_info.append("How Starlytics Recency Weighting works:\n\n", style="bold yellow")
                settings_info.append("", style="bold yellow")
                settings_info.append(f"[OFF]", style="bold red")
                settings_info.append(
                    f" ➔ Calculates a standard HISTORICAL average. Every review counts exactly the same, whether it was posted today or a year ago. Perfect for overall reputation.")
                settings_info.append(f"\n\n[ON]", style="bold green")
                settings_info.append(
                    f" ➔ Prioritizes CURRENT performance. Reviews lose half their voting power every 90 days. Recent feedback dominates the score, while old reviews smoothly fade out. Perfect for spotting quick trends.\n\n",
                )
                settings_info.append("Current Recency Weighting Toggle Status: ", style="bold white")
                if engine.recency_weighting:
                    settings_info.append(f"[ON] (default: OFF)", style="green")
                else:
                    settings_info.append(f"[OFF] (default: OFF)", style="red")
                
                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: Recency Weighting Toggle [/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                console.print()
                
                while True:
                    try:
                        user_input = input("Change Recency Weighting Toggle (1 -> ON | 2 -> OFF): ")
                        if user_input == "1":
                            engine.recency_weighting = True
                        elif user_input == "2":
                            engine.recency_weighting = False
                        else:
                            raise ValueError
                        
                        console.print("\n✅ Recency Weighting Toggle status updated successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Enter 1 or 2 \n", style="bold red")
            
            elif option == "6":
                console.print(Rule(style="bright_cyan"))
                    
                settings_info = Text()
                settings_info.append("Why switch AI model?\n\n", style="bold yellow")
                
                settings_info.append("Starlytics lets you swap the underlying processing engine depending on your data volume and API health:\n\n", style="white")
                
                settings_info.append("⚡ gemini-2.5-flash (Default)\n", style="bold cyan")
                settings_info.append("  • Faster.\n", style="white")
                settings_info.append("  • Optimized for extreme speed and real-time dashboard execution.\n", style="white")
                settings_info.append("  • Note: Because it is the default model for millions of developers, its servers face massive traffic spikes, making it more prone to temporary outages.\n\n", style="dim white")
                
                settings_info.append("🧠 gemini-2.5-pro\n", style="bold cyan")
                settings_info.append("  • Slower.\n", style="white")
                settings_info.append("  • Designed for deep, complex reasoning, nuance, and advanced sentiment pattern detection.\n", style="white")
                settings_info.append("  • Runs on separate, isolated server infrastructure away from the standard free-tier noise.\n", style="white")
                
                settings_info.append("\n🌐 What is a 503 Server Error?\n", style="bold orange3")
                settings_info.append("A 503 error means Google's specific model backend is temporarily overloaded or down (Service Unavailable). \n\n", style="white")

                settings_info.append("💡 Recommendation: ", style="bold green")
                settings_info.append(
                    "Stick to Flash for standard dashboard use. If you hit a persistent 503 Server Error, switch to another model.", style="white"
                )

                settings_info.append(f"\n\nCurrent AI model: ", style="bold white")
                settings_info.append(f"{engine.ai_model}", style="cyan")
                
                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: Change AI model [/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                console.print()
                
                while True:
                    try:
                        user_input = input("Change AI model (1 -> gemini-2.5-flash | 2 -> gemini-2.5-pro): ")
                        if user_input == "1":
                            engine.ai_model = "gemini-2.5-flash"
                        elif user_input == "2":
                            engine.ai_model = "gemini-2.5-pro"
                        else:
                            raise ValueError
                        
                        console.print("\n✅ AI model changed successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Enter 1 or 2 \n", style="bold red")
            
            elif option == "7":
                console.print(Rule(style="bright_cyan"))
                
                settings_info = Text()
                settings_info.append("🔐 Gemini API Key Configuration\n\n", style="bold yellow")
                
                settings_info.append("Starlytics relies on Google Gemini's large language models to analyze most frequent keywords and provide strategy based on them\n\n", style="white")
                
                settings_info.append("📊 Understanding Free Tier Quotas:\n", style="bold cyan")
                settings_info.append("• Google AI Studio grants 20 requests per day (RPD) on standard free projects.\n", style="white")
                settings_info.append("• If your application throws a persistent 429 Resource Exhausted error, your current key has hit its daily ceiling.\n\n", style="white")
                
                settings_info.append("💡 Developer Tip: ", style="bold green")
                settings_info.append(
                    "If you exhaust your daily limit, you can swap to a fresh API token from a secondary Google account and paste it here to bypass the restriction instantly without restarting Starlytics.\n", 
                    style="white"
                )

                current_key = os.environ.get("GEMINI_API_KEY")
                settings_info.append("\nCurrent Status: ", style="bold white")
                if current_key:
                    masked_key = f"...{current_key[-4:]}" if len(current_key) > 4 else "Active"
                    settings_info.append(f"Connected (Key: {masked_key})", style="bold green")
                else:
                    settings_info.append("Not Configured (AI features will fail)", style="bold red")
                
                console.print(Panel(
                    settings_info,
                    title="[bold bright_cyan] Settings: Set Gemini API Key [/bold bright_cyan]",
                    border_style="bright_cyan",
                    padding=(1, 2),
                    width=70
                ))
                
                while True:
                    try:
                        user_input = input("Paste your Gemini API Key (Press Enter to exit this setting): ")
                        if not user_input:
                            settings_mode()

                        os.environ["GEMINI_API_KEY"] = user_input
    
                        console.print("\n✅ Gemini API Key set successfully!\n", style="bold green")
                        settings_mode()
                    except ValueError:
                        console.print("\n❌ Invalid Input: Cannot proceed without an API Key. \n", style="bold red")
            elif not option:
                main()
            else:
                raise ValueError
            break
        except ValueError:
            print("Invalid Input")

def get_period():
    while True:
        try:
            analysis_text = (
                "[cyan]1[/cyan] ➔ Last Week\n"
                "[cyan]2[/cyan] ➔ Last Month\n"
                "[cyan]3[/cyan] ➔ Last 6 Months\n"
                "[cyan]4[/cyan] ➔ All Period\n"
                "[cyan]5[/cyan] ➔ Enter Custom Period"
            )
            
            console.print(Panel(
                analysis_text, 
                title="[bold bright_cyan] ANALYSIS PERIOD [/bold bright_cyan]", 
                expand=False, 
                padding=(1, 3)
            ))
            
            time_period = Prompt.ask(
                "[bold white]Choose Analysis Period[/bold white]", 
                choices=["1", "2", "3", "4", "5"]
            )
            if time_period == "1":
                time_period = datetime.timedelta(weeks=1)
                period_end = datetime.datetime.now()
                period_start = period_end-time_period
            elif time_period == "2":
                time_period = datetime.timedelta(days=30)
                period_end = datetime.datetime.now()
                period_start = period_end-time_period
            elif time_period == "3":
                time_period = datetime.timedelta(days=183)
                period_end = datetime.datetime.now()
                period_start = period_end-time_period
            elif time_period == "4":
                period_end = datetime.datetime(year=3000, month=1, day=1, hour=0, minute=0, second=0)
                period_start = datetime.datetime(year=1900, month=1, day=1, hour=0, minute=0, second=0)
            elif time_period == "5":
                while True:
                    try:
                        while True:
                            try:
                                period_start = input("Enter start date and time (year-mm-dd hh:mm:ss): ")
                                if matches := re.search(r"^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$", period_start):
                                    period_start = datetime.datetime(year=int(matches.group(1)), month=int(matches.group(2)), day=int(matches.group(3)), hour=int(matches.group(4)), minute=int(matches.group(5)), second=int(matches.group(6)))
                                else:
                                    raise ValueError
                                break
                            except ValueError:
                                print("Invalid format")
                        while True:
                            try:
                                period_end = input("Enter end date (year-mm-dd hh:mm:ss): ")
                                if matches := re.search(r"^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$", period_end):
                                    period_end = datetime.datetime(year=int(matches.group(1)), month=int(matches.group(2)), day=int(matches.group(3)), hour=int(matches.group(4)), minute=int(matches.group(5)), second=int(matches.group(6)))
                                else:
                                    raise ValueError
                                
                                break
                            except ValueError:
                                print("Invalid format")

                        
                        if period_start > period_end:
                            raise ValueError
                        break
                    except ValueError:
                        print("Invalid Values: Start date is later than End date")
            else:
                raise ValueError
            break
        except ValueError:
            print("Invalid Input")  
    
    return (period_start, period_end)
    

def ingestor(period_start, period_end, file_name):
    all_reviews = []
    with open(file_name) as file:
        reader = csv.DictReader(file)

        reviews_count = 0
        for row in sorted(reader, key=lambda d: d["date_string"], reverse=True):
            
            if matches := re.search(r"^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$", row["date_string"]):
                date = datetime.datetime(year=int(matches.group(1)), month=int(matches.group(2)), day=int(matches.group(3)), hour=int(matches.group(4)), minute=int(matches.group(5)), second=int(matches.group(6)))
            
            review = Review(stars=row["stars"], text=row["review_text"], timestamp=date)

            if date >= period_start and date <= period_end:
                if reviews_count == 0:
                    last_review = review
                first_review = review
                reviews_count += 1
                
                all_reviews.append(review)

        try:
            print(f"""
###
Loaded {reviews_count} reviews from {first_review.timestamp} to {last_review.timestamp} date range. 
###
                """)
        except UnboundLocalError:
            console.print(Text(f"""
############################
NO DATA FOR THIS TIME PERIOD
############################ 
"""), style="bold red", justify="center")
            main()
            

    return (all_reviews, reviews_count)

def categorize_review(review):
    categories = set()
    text = review.text.lower()
    categories_count = 0
    for category_kw in categories_kw.keys():
        for key_word in categories_kw[category_kw]:
            if key_word in text:
                categories.add(category_kw)
                categories_count += 1
    if categories_count == 0:
        return {"Other"}
    else:
        return categories
    
def sentimentize_review(review):
    review_text_splitted = re.split(r"but|although|and|however|though|while|except|whereas|also|plus|besides|!|,|;|\.|\?|\n|\t", review.text.lower())
    sentiment_dict = {}

    for category_kw in review.category:
        sentiment_dict[category_kw] = []
        for phrase in review_text_splitted:
            score = analyzer.polarity_scores(phrase)
            score = refine_score(review, score["compound"])
            try:
                for key_word in categories_kw[category_kw]:
                    if key_word in phrase:
                        sentiment_dict[category_kw].append(score)
            except KeyError:
                sentiment_dict[category_kw].append(score)

        sentiment_dict[category_kw] = round(statistics.mean(sentiment_dict[category_kw]), 2)

    return sentiment_dict

def get_keywords(review):
    review_text_splitted = re.split(r"but|although|and|however|though|while|except|whereas|also|plus|besides|!|,|;|\.|\?|\n|\t", review.text.lower())
    positive_kw_dict = {}
    negative_kw_dict = {}

    for category_kw in review.category:
        positive_kw_dict[category_kw] = Counter()
        negative_kw_dict[category_kw] = Counter()
        for phrase in review_text_splitted:
            score = analyzer.polarity_scores(phrase)
            score = refine_score(review, score["compound"])
            words = phrase.split(" ")
            try:
                for key_word in categories_kw[category_kw]:
                    if key_word in words and not (key_word in umbrella_words[category_kw]):
                        if score >= 80:
                                positive_kw_dict[category_kw].update([key_word])
                        elif score <= 60: 
                            negative_kw_dict[category_kw].update([key_word])
            except KeyError:
                if score >= 80:
                    positive_kw_dict[category_kw].update([key_word])
                elif score <= 60: 
                    negative_kw_dict[category_kw].update([key_word])
    
    return (positive_kw_dict, negative_kw_dict)

def refine_score(review, score):
    stars = review.stars
    stars_to_vader = {
        "1": -1.0,
        "2": -0.5,
        "3": 0.0,
        "4": 0.5,
        "5": 1.0,
    }
    stars = stars_to_vader[stars]
    if review.text == "":
        score = ((stars + 1) / 2) * 100
    else:
        score = round(((stars*0.7 + score*0.3) + 1) / 2 * 100)
            
    return score

if __name__ == "__main__":
    main()