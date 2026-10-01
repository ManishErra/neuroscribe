export default function BrandSignature() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed bottom-2 left-0 right-0 z-40 flex flex-col items-center gap-1"
    >
      <img
        src="/neuroscribe-signature-logo.png"
        alt=""
        className="h-5 w-auto object-contain opacity-50"
      />
      <span className="text-[10px] font-medium tracking-wide text-muted-foreground/45">
        Manish. O Erra
      </span>
    </div>
  );
}
