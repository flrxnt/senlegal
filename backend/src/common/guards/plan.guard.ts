import { CanActivate, ExecutionContext, ForbiddenException, Injectable } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Plan } from '@prisma/client';
import { REQUIRED_PLAN_KEY } from '../decorators/require-plan.decorator';

@Injectable()
export class PlanGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) { }

  canActivate(context: ExecutionContext): boolean {
    const required = this.reflector.getAllAndOverride<Plan[] | undefined>(REQUIRED_PLAN_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!required || required.length === 0) return true;
    const req = context.switchToHttp().getRequest();
    const user = req.user as { plan?: Plan } | undefined;
    if (!user?.plan || !required.includes(user.plan)) {
      throw new ForbiddenException('Cette fonctionnalité nécessite un abonnement supérieur.');
    }
    return true;
  }
}
