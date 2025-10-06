import Head from "next/head";
import dynamic from "next/dynamic";

const AuditPage = dynamic(() => import("../components/AuditPage"), { ssr: false });

export default function Home() {
  return (
    <>
      <Head>
        <title>CannaHealth Audit</title>
        <meta name="description" content="CannaHealth audit dashboard" />
      </Head>
      <main>
        <AuditPage />
      </main>
    </>
  );
}
