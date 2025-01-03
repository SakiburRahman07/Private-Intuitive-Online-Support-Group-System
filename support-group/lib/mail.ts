import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export const sendTwoFactorTokenEmail = async (email: string, token: string) => {
  await resend.emails.send({
    from: 'Sakib <onboarding@resend.dev>',
    to: email,
    subject: "Two step verification",
    html: `<p>Your two step verification code : ${token} </p>`
  });
}



export const sendPasswordResetEmail = async (email: string, token: string) => {
  const resetLink = `http://localhost:3000/auth/new-password?token=${token}`;

  await resend.emails.send({
    from: 'Sakib <onboarding@resend.dev>',
    to: email,
    subject: "Confirm Your Email",
    html: `<p>Click <a href="${resetLink}">here</a> to confirm email. </p>`
  });



};


export const sendVerificationEmail = async (email: string, token: string) => {
  const confirmLink = `http://localhost:3000/auth/new-verification?token=${token}`;

  await resend.emails.send({
    from: 'Sakib <onboarding@resend.dev>',
    to: email,
    subject: "Confirm Your Email",
    html: `<p>Click <a href="${confirmLink}">here</a> to confirm email. </p>`
  });
};