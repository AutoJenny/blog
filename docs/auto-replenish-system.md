# Auto-Replenish System

The auto-replenish system automatically maintains queue levels by adding items when they fall below configured thresholds.

## How It Works

1. **Daily Cron Job**: Runs every day at 9:00 AM
2. **Queue Check**: Checks each configured queue type for current item count
3. **Auto-Replenish**: If count is below threshold, adds items to bring it up to the threshold
4. **Logging**: All actions are logged to `/logs/auto-replenish.log`

## Configuration

Edit `/config/queue_auto_replenish.json` to configure queue types:

```json
{
  "enabled": true,
  "queues": [
    {
      "type": "product",
      "platform": "facebook",
      "threshold": 9,
      "add_count": 10,
      "enabled": true
    },
    {
      "type": "blog",
      "platform": "facebook", 
      "threshold": 5,
      "add_count": 8,
      "enabled": true
    }
  ]
}
```

### Configuration Options

- **enabled**: Global enable/disable for the entire system
- **type**: Queue content type (product, blog, etc.)
- **platform**: Social media platform (facebook, instagram, etc.)
- **threshold**: Minimum number of items to maintain
- **add_count**: Number of items to add when replenishing
- **enabled**: Enable/disable individual queue types

## Manual Testing

Test the system manually:

```bash
# Run the test script
./test-auto-replenish.sh

# Or call the endpoint directly
curl -X POST http://localhost:5000/launchpad/api/auto-replenish-all
```

## Cron Job Management

View current cron jobs:
```bash
crontab -l
```

Edit cron jobs:
```bash
crontab -e
```

Remove cron jobs:
```bash
crontab -r
```

## Logs

Check auto-replenish logs:
```bash
tail -f logs/auto-replenish.log
```

## Adding New Queue Types

1. Add the queue configuration to `/config/queue_auto_replenish.json`
2. Ensure the queue type exists in your `posting_queue` table
3. Test manually before relying on the cron job

## Troubleshooting

- **Cron job not running**: Check if cron service is running (`sudo service cron status`)
- **Endpoint not responding**: Ensure Flask app is running on port 5000
- **Configuration errors**: Check JSON syntax in config file
- **Database errors**: Check database connection and table structure
