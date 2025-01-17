import argparse


def parse_arguments(policies: list[str], default_co2: int):
    parser = argparse.ArgumentParser(
        description="Configure company CO2 budgets and policies."
    )

    # Add arguments
    parser.add_argument(
        "--num_workers_per_company",
        type=int,
        default=30,
        help="Number of workers per company (default: 30)",
    )

    for policy in policies:
        parser.add_argument(
            f"--{policy}",
            type=int,
            default=0,
            help=f"Number of companies with {policy} (default: 0)",
        )

    parser.add_argument(
        "--company_budget_per_employee",
        type=float,
        default=default_co2,
        help=f"Default CO2 budget per employee in grams (default: {default_co2})",
    )

    return parser.parse_args()


def get_companies(args, policies):
    companies = {
        policy: getattr(args, policy)
        for policy in policies
        if getattr(args, policy) is not None
    }
    if sum(companies.values()) == 0:
        raise ValueError(f"Invalid number of companies: {companies}")
    return companies


if __name__ == "__main__":
    policies = ["policy0", "policy1", "policy2"]
    args = parse_arguments(policies, 1000)

    companies = get_companies(args, policies)

    print(f"Number of workers per company: {args.num_workers_per_company}")
    print(f"Companies: {companies}")
    print(f"Company budget per employee: {args.company_budget_per_employee}")
