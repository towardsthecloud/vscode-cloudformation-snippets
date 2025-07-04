# AWS CloudFormation Snippets for VS Code

[![](https://img.shields.io/visual-studio-marketplace/v/dannysteenman.cloudformation-yaml-snippets?color=374151&label=Visual%20Studio%20Marketplace&labelColor=000&logo=visual-studio-code&logoColor=0098FF)](https://marketplace.visualstudio.com/items?itemName=dannysteenman.cloudformation-yaml-snippets)
[![](https://img.shields.io/visual-studio-marketplace/v/dannysteenman.cloudformation-yaml-snippets?color=374151&label=Open%20VSX%20Registry&labelColor=000&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0idXRmLTgiPz4KPHN2ZyB2aWV3Qm94PSI0LjYgNSA5Ni4yIDEyMi43IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgogIDxwYXRoIGQ9Ik0zMCA0NC4yTDUyLjYgNUg3LjN6TTQuNiA4OC41aDQ1LjNMMjcuMiA0OS40em01MSAwbDIyLjYgMzkuMiAyMi42LTM5LjJ6IiBmaWxsPSIjYzE2MGVmIi8+CiAgPHBhdGggZD0iTTUyLjYgNUwzMCA0NC4yaDQ1LjJ6TTI3LjIgNDkuNGwyMi43IDM5LjEgMjIuNi0zOS4xem01MSAwTDU1LjYgODguNWg0NS4yeiIgZmlsbD0iI2E2MGVlNSIvPgo8L3N2Zz4=&logoColor=0098FF)](https://open-vsx.org/extension/dannysteenman/cloudformation-yaml-snippets)
[![Installs](https://img.shields.io/visual-studio-marketplace/i/dannysteenman.cloudformation-yaml-snippets 'Currently Installed')](https://marketplace.visualstudio.com/items?itemName=dannysteenman.cloudformation-yaml-snippets)
[![Rating](https://img.shields.io/visual-studio-marketplace/stars/dannysteenman.cloudformation-yaml-snippets)](https://marketplace.visualstudio.com/items?itemName=dannysteenman.cloudformation-yaml-snippets)

This CloudFormation Snippets extension equips Visual Studio Code with JSON and YAML snippets for **all** AWS CloudFormation and SAM resources - over 1250+ in total. It's your complete toolset for efficient CloudFormation template development.

<!-- TIP-LIST:START -->
> [!TIP]
> **[Towards the Cloud](https://towardsthecloud.com/about) eliminates AWS complexity so you ship faster with confidence, cut costs by 30%, and become compliant.**
>
> Sounds too good to be true? We'll assess your AWS account for free and report exactly where you stand. You'll receive a report with security findings and cost optimization opportunities. After that you can decide whether to fix these findings yourself or let us handle it. No strings attached.
>
> <a href="https://cal.com/towardsthecloud/aws-account-review"><img alt="Book a Free AWS Account Review" src="https://img.shields.io/badge/Book%20A%20Free%20AWS%20Account%20Review-success.svg?style=for-the-badge"/></a>
>
> <details>
> <summary>☁️ <strong>Discover how we cut AWS costs by 30% and accelerate SOC 2 compliance...</strong></summary>
> <br/>
>
> ### AWS complexity builds faster than you realize
>
> What starts as simple deployment quickly spirals into inefficient architectures costing 40-60% more than needed, security blind spots risking customer data, and team burnout from operations instead of product development.
>
> **Traditional consultancies prioritize billable hours over outcomes, then disappear after setup. We do the opposite...**
>
> ---
>
> ### We provide a complete package, so you deploy faster with confidence on AWS Cloud
>
> - ✅ **[Compliant multi-account Landing Zone](https://towardsthecloud.com/services/aws-landing-zone)**:
>   - Provisions AWS accounts with security guardrails out of the box - 100% [CIS benchmark compliant](https://docs.aws.amazon.com/securityhub/latest/userguide/cis-aws-foundations-benchmark.html)
>   - Secure Single Sign-On (SSO) for clean user access management
>   - Everything is built using AWS CDK ensuring consistency, version control, and repeatable deployments
>   - See what features are already included in our landing zone on our [public roadmap](https://github.com/towardsthecloud/aws-cdk-landing-zone-roadmap?tab=readme-ov-file#features)
> - ✅ **Off-the-shelf compliant CDK components**: Develop secure infra quicker without reinventing the wheel
> - ✅ **Complete CI/CD with easy rollbacks**: Deploy more frequently because of IaC safety
> - ✅ **Quarterly checks**: Proactively receive [Cost Optimization assessments](https://towardsthecloud.com/services/aws-cost-optimization) + [Security Reviews](https://towardsthecloud.com/services/aws-security-review)
> - ✅ **Fractional Cloud Engineer**: On-demand access to a decade of AWS Cloud experience to help you use best practices
>
> ---
>
> ### What results can you expect when you partner with us:
>
> - **30% Lower AWS Bill**: Proactive quarterly reviews catch overspending before it happens [(30-60% documented savings)](https://towardsthecloud.com/services/aws-cost-optimization#case-study)
> - **Accelerate SOC 2/HIPAA compliance**: Our Landing Zone automatically sets up security guardrails on your AWS accounts with 100% CIS compliance from day one
> - **Easily stay compliant**: Our automated monitoring and proactive quarterly security reviews give you control so yearly audits are smooth, not stressful
> - **Your Team Ships Faster**: Our Pre-built secure infrastructure components let your team focus on product, not AWS
> - **Save on hiring costs**: Access expert Cloud knowledge through our [flexible retainer](https://towardsthecloud.com/pricing) instead of committing to a full-time Cloud Engineer
>
> **Proof:** Y Combinator startup Accolade's founder on how our Landing Zone [accelerated their SOC 2 certification](https://towardsthecloud.com/blog/aws-landing-zone-case-study-accolade):
>
> *"Danny's solution and AWS expertise stood out with comprehensive accelerators, documentation, and clearly articulated design principles. **We achieved a perfect security score in days, not months.**"* — Galen Simmons, CEO
>
> </details>
<!-- TIP-LIST:END -->

---

## Features

1. **Comprehensive Coverage**: Offers snippets for **all** AWS CloudFormation and AWS SAM resources available - that's over 1250+ resources snippets at your fingertips!
2. **Complete Property Support**: Includes all nested properties for each resource, ensuring you have access to every configurable aspect of your AWS resources.
3. **Documentation Hover Links**: Quickly access AWS CloudFormation resource and property documentation by hovering over resource types and property names in your templates.
4. **Flexible Template Support**: Seamlessly works with both YAML and JSON CloudFormation templates.
5. **Efficient Autocomplete**: Simply type the resource name (e.g., `ec2-instance`) to instantly load the corresponding snippet for `AWS::EC2::Instance`.
6. **Rich Feature Set**: Incorporates intrinsic functions, conditions, and diverse parameter types for robust template creation.
7. **Enhanced Navigation**: Features placeholders that enable swift movement through resource properties.
8. **Resource Documentation**: Each snippet is linked to its official AWS documentation, providing quick access to detailed information.
9. **Up-to-Date**: Regularly refreshed on a weekly basis to reflect the latest [CloudFormation Resource Specification](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-resource-specification.html).
10. **Gitpod Ready**: Made available on the [Open VSX Registry](https://open-vsx.org/extension/dannysteenman/cloudformation-yaml-snippets) to ensure compatibility with [Gitpod](https://github.com/towardsthecloud/vscode-cloudformation-snippets/issues/14).

## Usage

1. Install the [CloudFormation Snippets extension](https://marketplace.visualstudio.com/items?itemName=dannysteenman.cloudformation-yaml-snippets) in VS Code.
2. Create a new `.yml` or `.json` file.
3. Ensure the file type is set to "YAML" or "JSON" in the bottom right corner of VS Code.
4. Type cfn to insert the basic CloudFormation template structure.
5. Add resources using their short prefix (e.g. `s3-bucket` for `AWS::S3::Bucket`).

Example of auto-completion in action:

![CloudFormation Snippets example](https://raw.githubusercontent.com/dannysteenman/vscode-cloudformation-snippets/main/images/cfn-snippets-extension-example.gif)

and an example of the hover information:

![IAM Actions Snippets Hover Example](https://raw.githubusercontent.com/dannysteenman/vscode-cloudformation-snippets/main/images/cfn-snippets-hover-example.gif)

> **Note:** Once you start typing a prefix (explained in step 5), the corresponding snippet will show up in the dropdown menu. If this doesn't happen automatically, press `ctrl + space` to invoke IntelliSense and search for the prefix of the resource type that you want to add (as listed in step 5).

---
## AWS CloudFormation Starterkit

We've developed the [AWS CloudFormation Starterkit](https://github.com/towardsthecloud/aws-cloudformation-starterkit) to streamline your infrastructure setup using CloudFormation.

It comes with pre-configured templates, automated validation scripts, and seamless integration with CI/CD pipelines, you'll be able to deploy robust, scalable, and secure AWS environments with ease.

The starterkit empowers you to adopt best practices effortlessly. By leveraging tools like Checkov for security compliance and cfn-lint for template validation, you ensure that your infrastructure is both reliable and secure.

---
## Support

If you have a feature request or an issue, please let me know on [Github](https://github.com/towardsthecloud/vscode-cloudformation-snippets/issues)

## Author

[Danny Steenman](https://towardsthecloud.com/about)

[![](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/company/towardsthecloud)
[![](https://img.shields.io/badge/X-000000?style=for-the-badge&logo=x&logoColor=white)](https://twitter.com/dannysteenman)
[![](https://img.shields.io/badge/GitHub-2b3137?style=for-the-badge&logo=github&logoColor=white)](https://github.com/towardsthecloud)
