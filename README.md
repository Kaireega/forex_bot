# Forex Bot

An automated Forex trading bot for analyzing and executing trading strategies.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Repository Structure](#repository-structure)
- [Key Files](#key-files)
- [Getting Started](#getting-started)
- [Contributing](#contributing)
- [License](#license)

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Kaireega/forex_bot.git
cd forex_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

To start the trading bot:

```bash
python main.py
```

## Features

- Real-time Forex data scraping
- Technical analysis indicators
- Automated trade execution

## Repository Structure

- **analysis/**: Contains scripts and notebooks for analyzing Forex data, including statistical evaluations and visualizations.
- **api/**: Manages interactions with external APIs, such as Forex data providers and trading platforms.
- **bot/**: Implements the core trading bot logic, encompassing strategy execution and trade management.
- **constants/**: Defines constant variables and configurations used across the project.
- **db/**: Handles database operations, including data storage and retrieval mechanisms.
- **exploration/**: Includes exploratory data analysis scripts and experimental code.
- **forex-dash/**: Develops a dashboard for monitoring trading activities and performance metrics.
- **infrastructure/**: Manages infrastructure-related scripts, such as deployment configurations and environment setups.
- **models/**: Contains machine learning models and trading algorithms for predictive analysis.
- **scraping/**: Implements web scraping tools to collect Forex data from various sources.
- **simulation/**: Provides simulation environments for backtesting trading strategies.
- **stream_bot/**: Develops a bot for streaming real-time Forex data and executing trades accordingly.
- **stream_example/**: Offers example scripts demonstrating streaming data handling.
- **technicals/**: Includes technical analysis indicators and related tools.

## Key Files

- **.gitignore**: Specifies files and directories to be excluded from version control.
- **api_tests.py**: Contains test cases for validating API interactions.
- **main.py**: Serves as the main entry point for the application.
- **requirements.txt**: Lists the Python dependencies required for the project.
- **run_bot.py**: Script to initiate the trading bot.
- **scraping_tests.py**: Includes test cases for the web scraping modules.
- **server.py**: Manages server-related functionalities, possibly for the dashboard or API services.

## Getting Started

1. Clone the Repository:

   ```bash
   git clone https://github.com/Kaireega/forex_bot.git
   ```

2. Navigate to the Project Directory:

   ```bash
   cd forex_bot
   ```

3. Set Up a Virtual Environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install Dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the Main Application:

   ```bash
   python main.py
   ```

## Contributing

Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or issues, please open an issue in the repository or contact me at [your email].
