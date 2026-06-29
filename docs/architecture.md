# Architecture Diagram

```
                          ┌─────────────────────────────────────────────────────┐
                          │                  AWS ap-southeast-2                  │
                          │                                                       │
                          │   ┌───────────────────────────────────────────────┐  │
                          │   │                  VPC 10.0.0.0/16              │  │
                          │   │                                               │  │
  ┌──────────┐            │   │  ┌──────────────────────────────────────────┐ │  │
  │          │  HTTP :80  │   │  │           Public Subnets                  │ │  │
  │ Internet │ ─────────────────▶│  10.0.1.0/24 (AZ-a) · 10.0.2.0/24 (AZ-b) │ │  │
  │          │            │   │  │                                           │ │  │
  └──────────┘            │   │  │   ┌────────────────────────────────┐     │ │  │
                          │   │  │   │  Application Load Balancer      │     │ │  │
                          │   │  │   │  (internet-facing, multi-AZ)    │     │ │  │
                          │   │  │   └───────────────┬────────────────┘     │ │  │
                          │   │  │                   │ HTTP :80              │ │  │
                          │   │  │   ┌───────────────▼────────────────┐     │ │  │
                          │   │  │   │         Target Group            │     │ │  │
                          │   │  │   │   health-check GET / (HTTP 200) │     │ │  │
                          │   │  │   └───────────┬────────┬───────────┘     │ │  │
                          │   │  │               │        │                  │ │  │
                          │   │  └───────────────┼────────┼──────────────────┘ │  │
                          │   │                  │        │                     │  │
                          │   │  ┌───────────────┼────────┼──────────────────┐  │  │
                          │   │  │          Private Subnets                   │  │  │
                          │   │  │  10.0.11.0/24 (AZ-a) · 10.0.12.0/24 (AZ-b) │  │  │
                          │   │  │               │        │                   │  │  │
                          │   │  │  ┌────────────▼──┐  ┌─▼─────────────┐    │  │  │
                          │   │  │  │  EC2 (AZ-a)   │  │  EC2 (AZ-b)   │    │  │  │
                          │   │  │  │  t3.micro      │  │  t3.micro      │    │  │  │
                          │   │  │  │  Docker+NGINX  │  │  Docker+NGINX  │    │  │  │
                          │   │  │  └───────┬────────┘  └───────┬───────┘    │  │  │
                          │   │  │          └──────────┬─────────┘           │  │  │
                          │   │  │                     │ outbound only        │  │  │
                          │   │  │              ┌──────▼──────┐              │  │  │
                          │   │  │              │ NAT Gateway  │              │  │  │
                          │   │  │              │ (AZ-a, EIP)  │              │  │  │
                          │   │  │              └──────┬───────┘              │  │  │
                          │   │  └─────────────────────┼──────────────────────┘  │  │
                          │   │                        │                          │  │
                          │   │  ┌─────────────────────┼──────────────────────┐  │  │
                          │   │  │       Public Subnet  │                      │  │  │
                          │   │  │              ┌───────▼──────┐               │  │  │
                          │   │  │              │ Internet GW   │               │  │  │
                          │   │  │              └──────┬────────┘               │  │  │
                          │   │  └─────────────────────┼──────────────────────┘  │  │
                          │   └────────────────────────┼──────────────────────────┘  │
                          └────────────────────────────┼────────────────────────────┘
                                                       │
                                               ┌───────▼──────┐
                                               │   Internet    │
                                               │ (package DL,  │
                                               │  GHCR pull)   │
                                               └──────────────┘
```

## Auto-healing flow

1. EC2 instance becomes unhealthy (crash, termination, failed health check).
2. ALB stops routing traffic to that instance within ~30 s (2 consecutive health check failures).
3. ASG detects the instance is unhealthy and terminates it.
4. ASG launches a replacement in the same or alternate AZ to restore `desired_capacity`.
5. New instance runs user-data, starts NGINX/Docker, and passes health checks.
6. ALB adds the new instance to rotation — zero-downtime replacement.

## Security boundaries

| Layer | Ingress | Egress |
|-------|---------|--------|
| ALB SG | TCP 80 from `0.0.0.0/0` | all |
| EC2 SG | TCP 80 from ALB SG only | all (NAT) |
| Private NACL | VPC CIDR + ephemeral ports (deny 22) | all (deny 22) |
