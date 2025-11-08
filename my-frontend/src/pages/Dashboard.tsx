import WalletTable from "../components/WalletTable";

export default function Dashboard() {
  return (
    <main className="max-w-6xl mx-auto px-4 py-6">
      <h2 className="text-xl font-semibold mb-4">Mon portefeuille</h2>
      <WalletTable />
    </main>
  );
}
