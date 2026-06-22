# cicd-demo

Deliberately vulnerable CI/CD demo repo for the DEF CON 34 Red Team Village workshop.

Fork this repo and open a pull request to see the `pull_request_target` misconfiguration in action. Your workflow run will print live AWS STS credentials to the log — by design. This is the real-world CVE pattern used in tj-actions, GhostAction, and TeamPCP.

Do not copy this workflow into anything you care about.
trigger artifact run 1782149308
final screenshot run 1782149661
terminal screenshot run 1782150894
