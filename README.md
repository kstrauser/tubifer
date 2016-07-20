# Calculate and display ISP data plan prices

ISP data plans are difficult to compare. Tubifer intends to fix that. Its main components are:

* `tubifer/data/*.json`: formatted descriptions of ISPs and their available data plans
* A command, `show-data-prices`, for parsing and displaying the ISP descriptions

# Example

The `show-data-prices` command loads the data in `tubifer/data/*.json` and renders it in a readable format. By default, it displays information about all defined providers and all of their plans:

```text
$ show-data-prices --help

Usage: show-data-prices [OPTIONS] [PROVIDER_NAME] [TYPE_NAME] [PLAN_NAME]
                        [OPTION_NAME]

  Show ISP data plan prices on one or provider options.

  By default, show-data-prices displays all defined options for all
  providers. Results may be increasingly narrowed by giving provider, type,
  plan, and option names.

  If --usage-gb is given, plan options will display the calculated price for
  using that amount of data in a month.

  "Usage hours" are the number of hours each month you can use a plan option
  at full speed without exceeding its data cap.

Options:
  --state TEXT        State to show plans for
  --city TEXT         City to show prices for
  --usage-gb INTEGER  Expected data usage in GB
  --help              Show this message and exit.

$  show-data-prices

Provider: Verizon

  Type: LTE
    Sources:
      Speed: https://business.verizonwireless.com/content/b2b/en/4glte/4gltefaqs.html

    Plan: Verizon Plan
      Description: https://www.verizonwireless.com/landingpages/verizon-plan/

      Option: 2GB
        Base price: $35/month
        Cap GB: 2
        Max Mbps: 12
        Usage hours: 0.4

      Option: 4GB
        Base price: $50/month
        Cap GB: 4
        Max Mbps: 12
        Usage hours: 0.8

    [...]
```

You can successively narrow the results down by provider name, type name, plan name, and option name:

```text
$ show-data-prices Verizon LTE "Verizon Plan" 8GB

Provider: Verizon

  Type: LTE
    Sources:
      Speed: https://business.verizonwireless.com/content/b2b/en/4glte/4gltefaqs.html

    Plan: Verizon Plan
      Description: https://www.verizonwireless.com/landingpages/verizon-plan/

      Option: 8GB
        Base price: $70/month
        Cap GB: 8
        Max Mbps: 12
        Usage hours: 1.6
```

You can use the `--usage-gb` option to calculate how much each data plan can be expected to cost if you were to use that many GB of data in a month:

```text
$ show-data-prices Verizon LTE "Verizon Plan" 8GB --usage-gb 10

Provider: Verizon

  Type: LTE
    Sources:
      Speed: https://business.verizonwireless.com/content/b2b/en/4glte/4gltefaqs.html

    Plan: Verizon Plan
      Description: https://www.verizonwireless.com/landingpages/verizon-plan/

      Option: 8GB
        Base price: $70/month
        Extended price: $100/month
        Cap GB: 8
        Max Mbps: 12
        Usage hours: 1.6
```

# About Usage Hours

Many ISPs apply data caps to their plans. If a plan's option includes such a cap, its display will include a "usage hours" component whose value is the number of hours you could use that option at its highest advertised speed without exceeding its cap.

# Disclaimer

While we intend to keep this information as up-to-date as possible, ISP data contracts change constantly. Cell phone providers add and drop plans, cable companies selectively enforce data caps, etc. This information should be used only to get a high-level idea of the options available to you. Verify all information with your ISP before relying on it: if their numbers disagree with ours, theirs will be the ones that matter.

# Contributing

We'd love to receive new and updated data plan information from wide variety of ISPs! Submit changes as a GitHub pull request, being absolutely sure to document the sources of all data you add or change. It must be possible for a user to recreate all values used in calculations by visiting only URLs listed in the `type.sources` and `plan.description` dictionaries.

# License

Tubifer is distributable under the terms of the MIT License.
