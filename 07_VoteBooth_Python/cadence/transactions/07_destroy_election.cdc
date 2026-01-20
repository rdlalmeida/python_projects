/**
    This transaction uses an authorized reference to load and destroy an Election with the id provided as input argument.

    @param electionId (Uint64) The election identifier for the election to be destroyed
**/
import VoteBooth from 0x287f5c8b0865c516
import ElectionStandard from 0x287f5c8b0865c516
import Burner from 0x9a0766d93b6608b7

transaction(electionId: UInt64) {
    let electionIndexRef: &VoteBooth.ElectionIndex
    let electionStoragePath: StoragePath
    let electionPublicPath: PublicPath
    let electionToDestroy: @ElectionStandard.Election

    prepare(signer: auth(Storage, LoadValue, UnpublishCapability) &Account) {
        self.electionIndexRef = signer.storage.borrow<&VoteBooth.ElectionIndex>(from: VoteBooth.electionIndexStoragePath) ??
        panic(
            "Unable to retrieve a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `signer.address.toString()`"
        )

        self.electionStoragePath = self.electionIndexRef.getElectionStoragePath(electionId: electionId) ??
        panic(
            "Unable to retrieve a valid StoragePath for election `electionId.toString()` for the ElectionIndexPublic retrieved from account `signer.address.toString()`"
        )

        self.electionPublicPath = self.electionIndexRef.getElectionPublicPath(electionId: electionId) ??
        panic(
            "Unable to retrieve a valid PublicPath for election `electionId.toString()` for the ElectionIndexPublic retrieved from account `signer.address.toString()`"
        )

        self.electionToDestroy <- signer.storage.load<@ElectionStandard.Election>(from: self.electionStoragePath) ??
        panic(
            "Unable to retrieve a valid @ElectionStandard.Election at `self.electionStoragePath.toString()` from account `signer.address.toString()`"
        )

        // Unpublish all election capabilities
        let oldCapability: Capability? = signer.capabilities.unpublish(self.electionPublicPath)

        // Remove the election entry from the ElectionIndex
        let oldIndexEntry: {StoragePath: PublicPath}? = self.electionIndexRef.removeElectionFromIndex(electionId: electionId)
    }

    execute {
        // Finish with destroying the Election loaded with the Burner contract to trigger the Election's burnCallback
        Burner.burn(<- self.electionToDestroy)
    }
}