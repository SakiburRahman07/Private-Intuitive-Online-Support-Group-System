'use client';
import { CardWrapper } from './card-wrapper';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import * as z from "zod";
import { NewPasswordSchema } from '@/schemas';
import { Input } from '@/components/ui/input';

import { Button } from '@/components/ui/button';

import { FormSuccess } from '@/components/form-success';
import { useState } from 'react';

import { newPassword } from '@/actions/new-password';

import { useSearchParams } from 'next/navigation';

import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';

import { FormError } from '@/components/form-error';

import { useTransition } from 'react';
import Link from 'next/link';


export const NewPasswordForm = () => {
 const SearchParams = useSearchParams();
 const token = SearchParams.get('token');

  const [error, setError] = useState<string | undefined>("");
  const [success, setSuccess] = useState<string | undefined>("");

  const [isPending, startTransition] = useTransition();
  const form = useForm<z.infer<typeof NewPasswordSchema>>({
    resolver: zodResolver(NewPasswordSchema),
    defaultValues: {
      password: '',
    },
  });

  const onSubmit = (values: z.infer<typeof NewPasswordSchema>) => {
    setError("");
    setSuccess("");

    console.log(values);

    startTransition(() => {
      newPassword(values, token).then((data) => {
        setError(data?.error);
        setSuccess(data?.success);

      }
      );
    });
  }

  return (
    <CardWrapper
      headerLabel='Enter a new password'
      backButtonLabel="Back to login" backButtonHref='/auth/login'
      
      >
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}
          className='space-y-6'>

          <div className='space-y-4'>

            <FormField control={form.control} name='password'
              render={({ field }) =>
              (
                <FormItem>
                  <FormLabel>Password</FormLabel>
                  <FormControl>
                    <Input {...field}
                      disabled={isPending}
                      placeholder='******'
                      type='password'
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}>

            </FormField>

           

          </div>

          <FormError message={error } />
          <FormSuccess message={success} />

          <Button disabled={isPending} type='submit'
            className='w-full' >
            Reset Password
          </Button>

        </form>
      </Form>
    </CardWrapper>);
}